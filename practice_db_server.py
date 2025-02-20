from flask import Flask, jsonify
import psycopg2
from psycopg2 import sql

app = Flask(__name__)

DATABASE_URL = "postgresql://practice_xsfw_user:TgBx3Xb1YwNIdK9HBKNqVXRHhTrVsHSN@dpg-cuq78qdsvqrc73f808sg-a.frankfurt-postgres.render.com/practice_xsfw"

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

@app.route('/data', methods=['GET'])
def get_data():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cur = conn.cursor()
    cur.execute('SELECT username, secret_phraze FROM users')
    rows = cur.fetchall()

    colnames = [desc[0] for desc in cur.description]

    result = []
    for row in rows:
        result.append(dict(zip(colnames, row)))

    cur.close()
    conn.close()
    return jsonify(result)

@app.route('/calendar', methods=['GET'])
def get_complex_query():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cur = conn.cursor()
    query = '''
    SELECT "r".* FROM (SELECT "r"."id", CASE
                   WHEN vpsc.field_value IS NOT NULL THEN vpsc.field_value
                   ELSE r.name
                   END AS "name", "r"."no_time", "r"."button_action", "r"."status", "r"."procedure_id", "r"."procedure_general_number", "r"."procedure_secondary_number", "r"."procedure_inner_number", "r"."procedure_is_from_eis", "r"."procedure", CASE
                        WHEN lot_number IS NULL THEN procedure_general_number
                        ELSE procedure_general_number || '/' || lot_number::VARCHAR
                    END AS "event_full_number", "r"."procedure_name", "r"."archived", "r"."organizer_contragent_id", "r"."organizer_user_id", "r"."lot_id", "r"."lot_number", "r"."lot_name", "r"."order_number", "r"."customers", "r"."is_user_customer", "r"."is_user_organizer", "r"."contract_id", "r"."subprocedure_id", "r"."type_id", (to_char(r.date, 'YYYY-MM-DD"T"HH24:MI:SS.MS')|| to_char(extract('timezone_hour' from r.date),'S00')||':'|| to_char(extract('timezone_minute' from r.date),'FM00')) AS "date", to_char(actual_date, 'YYYY-MM-DD') AS "sorting_day", CASE
                        WHEN no_time IS TRUE THEN to_char(actual_date, 'YYYY-MM-DD"T"23:23:59.999') || '+03:00'
                        ELSE to_char(actual_date, 'YYYY-MM-DD"T"HH24:MI:SS.MS') || '+03:00'
                    END AS "sorting_date", (to_char(r.completed_date, 'YYYY-MM-DD"T"HH24:MI:SS.MS')|| to_char(extract('timezone_hour' from r.completed_date),'S00')||':'|| to_char(extract('timezone_minute' from r.completed_date),'FM00')) AS "completed_date", CASE
                        WHEN r.status = 'overdue'
                        THEN DATE_PART('day', 'today'::TIMESTAMPTZ - actual_date::DATE)
                    END AS "overdue_days", json_build_array(array_remove(array_remove(ARRAY[
                        procedure_general_number,
                        procedure_secondary_number,
                        remote_id,
                        procedure_number,
                        procedure_inner_number,
                        rpz_number
                    ], ''), NULL))->0 AS "search_keywords", CASE
                WHEN prot.oos_id IS NULL AND prot.oos_publish_status < 0 AND prot.status =
                    9 THEN 'Удалён в ЕИС'
                WHEN prot.oos_publish_status in (-1,1,3) THEN 'Ожидает публикации в ЕИС'
                 ELSE ''
                 END AS "oos_protocol_publish_status", "oc"."id" AS "organizer_id", "oc"."short_name" AS "organizer_name", "oc"."inn" AS "organizer_inn", "oc"."kpp" AS "organizer_kpp", "oc"."ogrn" AS "organizer_ogrn", concat_ws(' ', u.last_name::text, u.first_name::text, u.middle_name::text) AS "user_fullname", "u"."username" AS "user_username", CASE
                            WHEN r.procedure_is_from_eis = true THEN '-'
                            ELSE concat_ws(' ', u.last_name::text, u.first_name::text, u.middle_name::text,
                                concat('(', u.username::text ,')'))
                         END AS "publicator_user_info", "lsp"."order_number" AS "subprocedure_order_number", "vls"."id" AS "lot_statuses" FROM (SELECT DISTINCT ON (t.procedure_id, lot_number, t.type_id, t.completed_date IS NOT NULL,
                   t.contract_id, t.subprocedure_id) NULL, "t"."type_id", "t"."id", "t"."procedure_id", "t"."procedure_step_id", "t"."contract_id", "t"."subprocedure_id", "plc"."lots_count", "t"."lot_id", CASE
                    WHEN p.unified_protocol_for_all_lots IS TRUE AND t.subprocedure_id IS NULL
                     AND t.instance_type != 2 THEN NULL
                    ELSE l.number
                END AS "lot_number", CASE
                    WHEN completed_date IS NOT NULL THEN 'done'
                    WHEN (date at time zone 'UTC' + interval '180 minute') >= 'tomorrow'::TIMESTAMPTZ THEN 'upcoming'
                    WHEN date > NOW() THEN 'current'
                    WHEN l.status IN (2,12) AND (date + interval '5 minute') > NOW() THEN 'current'
                    WHEN l.status = 5 THEN 'current'
                    ELSE 'overdue'
                END AS "status", "ctt"."description" AS "name", "ctt"."no_time", "ctt"."action" AS "button_action", CASE
                    WHEN p.eis_registry_number IS NULL THEN p.registry_number
                    ELSE p.eis_registry_number
                END AS "procedure_general_number", CASE
                    WHEN p.eis_registry_number IS NULL OR p.registry_number = p.eis_registry_number THEN NULL
                    ELSE p.registry_number
                END AS "procedure_secondary_number", "p"."procedure_number2" AS "procedure_inner_number", CASE
                    WHEN p.eis_registry_number = p.registry_number THEN true
                    ELSE false
                END AS "procedure_is_from_eis", "p"."title" AS "procedure_name", "p"."remote_id", "p"."procedure_number", "p"."procedure_type", "p"."small_biz_only", "l"."rpz_number", "l"."waiting_commission_signature", "l"."subject" AS "lot_name", "l"."status" AS "lot_status", "p"."organizer_contragent_id", "p"."organizer_user_id", date at time zone 'UTC' + interval '180 minute' AS "actual_date", p.date_archived IS NOT NULL AS "archived", "lc"."customers", "lc"."is_user_customer", "p"."is_user_organizer", "p"."date_archived", "t"."date", "t"."completed_date", "ctt"."order_number", (plc.lots_count = 1) AS "single_lot", json_build_object(
                    'id', p.id,
                    'is_223_fz', p.is_223_fz,
                    'unified_protocol_for_all_lots', p.unified_protocol_for_all_lots,
                    'with_proc_consideration', p.with_proc_consideration,
                    'with_applic_consideration', p.with_applic_consideration,
                    'small_biz_only', p.small_biz_only,
                    'date_published', p.date_published,
                    'features', p.features,
                    'send_to_oos', p.send_to_oos,
                    'oos_publish_status', p.oos_publish_status,
                    'oos_cancel_status', p.oos_cancel_status,
                    'organizer_contragent_id', p.organizer_contragent_id,
                    'version', p.version,
                    'procedure_type', p.procedure_type,
                    'with_applic_correction', p.with_applic_correction,
                    'application_stages', p.application_stages,
                    'current_protocol_oos_publish_status', st.current_protocol_oos_publish_status,
                    'features', p.features,
                    'this_customer_can_see_applics', EXISTS(
                                                         SELECT true FROM contragent_features cf
                                                         INNER JOIN features f on cf.feature_id = f.id
                                                         WHERE cf.contragent_id = p.organizer_contragent_id
                                                          AND f.name = 'CUSTOMER_CAN_SEE_APPLICS'
                                                          AND cf.actual
                                                          AND (cf.date_begin IS NULL OR cf.date_begin <= NOW())
                                                          AND (cf.date_end IS NULL OR cf.date_end > NOW())
                                                         )
                                                     AND
                                                     EXISTS(
                                                         SELECT true FROM lots as l
                                                         INNER JOIN lot_customers as lc
                                                           ON lc.lot_id = l.id
                                                           AND (customer_id = 1 OR affiliate = 1)
                                                         WHERE p.id = l.procedure_id
                                                     )
                ) AS "procedure" FROM "calendar_todos" AS "t"
 INNER JOIN "vocab_calendar_todo_types" AS "ctt" ON t.type_id = ctt.id
 LEFT JOIN (SELECT "p".*, p.organizer_contragent_id IN (1) AS "is_user_organizer" FROM "procedures" AS "p") AS "p" ON t.procedure_id = p.id
 LEFT JOIN (SELECT "lots"."procedure_id", count(*) AS "lots_count" FROM "lots" GROUP BY "procedure_id") AS "plc" ON t.procedure_id = plc.procedure_id
 LEFT JOIN "lots" AS "l" ON t.lot_id = l.id
 LEFT JOIN "lot_stats" AS "lstat" ON lstat.lot_id = t.lot_id
 LEFT JOIN (SELECT "l"."procedure_id", "l"."lot_id", json_agg(DISTINCT jsonb_build_object(
                    'customer_id', c.id,
                    'customer_name', COALESCE(c.short_name, c.full_name),
                    'customer_inn', c.inn,
                    'customer_kpp', c.kpp,
                    'customer_ogrn', c.ogrn
                )) AS "customers", bool_or(c.id IN (1)) AS "is_user_customer" FROM "lot_customers" AS "lc"
 LEFT JOIN "contragents" AS "c" ON lc.customer_id = c.id
 LEFT JOIN (
               SELECT
                   id,
                   procedure_id,
                   CASE
                       WHEN row_number() OVER (PARTITION BY id) = 1 THEN id
                   END lot_id
               FROM lots, lateral generate_series(1, 2)
            ) AS "l" ON lc.lot_id = l.id WHERE (lc.actual IS TRUE) GROUP BY 1, 2) AS "lc" ON t.procedure_id = lc.procedure_id
                 AND (
                     (p.unified_protocol_for_all_lots IS TRUE AND t.subprocedure_id IS NULL AND lc.lot_id IS NULL)
                     OR ((p.unified_protocol_for_all_lots IS FALSE OR t.subprocedure_id IS NOT NULL) AND t.lot_id = lc.lot_id)
                 )
 LEFT JOIN "procedure_stats" AS "st" ON p.id = st.procedure_id WHERE ((ctt.pseudo = 'trade-start'
                AND (l.status IN (2,12)
              OR lstat.applics_count > 1)) OR ctt.pseudo <> 'trade-start') AND ((is_user_organizer IS TRUE AND ctt.type = 1) OR ((is_user_customer IS TRUE OR (is_user_customer IS NULL AND is_user_organizer IS TRUE)) AND ctt.type = 2)) AND (p.actual IS TRUE) AND (l.actual IS TRUE)) AS "r"
 LEFT JOIN "contragents" AS "oc" ON r.organizer_contragent_id = oc.id
 LEFT JOIN "users" AS "u" ON r.organizer_user_id = u.id
 LEFT JOIN "lot_subprocedures" AS "lsp" ON lsp.id = r.subprocedure_id
 LEFT JOIN "procedure_steps" AS "ps" ON ps.id = r.procedure_step_id
 LEFT JOIN "vocab_procedure_steps" AS "vps" ON vps.pseudo = ps.step_id
 LEFT JOIN "vocab_procedure_steps_custom" AS "vpsc" ON vpsc.procedure_type = r.procedure_type AND vpsc.step_pseudo = ps.step_id
               AND field_name = CASE
                            WHEN ps.date_start is not null AND r.small_biz_only = true THEN 'full_name_start_msp'
                            WHEN ps.date_start is not null AND r.small_biz_only = false THEN 'full_name_start'
                            WHEN ps.date_end is not null AND r.small_biz_only = true THEN 'full_name_end_msp'
                            ELSE 'full_name_end'
                         END
 LEFT JOIN "vocab_lot_statuses" AS "vls" ON vls.id = vps.status
 LEFT JOIN "protocol" AS "prot" ON prot.procedure_id = r.procedure_id
                 AND (prot.lot_id IS NULL OR (r.single_lot AND prot.lot_id = r.lot_id))
                 AND ((prot.subprocedure_id IS NULL AND r.subprocedure_id IS NULL) OR prot.subprocedure_id = r.subprocedure_id)
                 AND prot.status IN (4,9)
                 AND (
                   (
                       vps.status = 5
                       AND prot.type in
                       (5,44,45,46,47,48,501)
                   )
                   OR (
                       vps.status = 3
                       AND prot.type in
                        (3,83)
                      )
                   OR (
                       vps.status = 6
                       AND prot.type in
                        (6,62)
                      )
                   OR (
                          vps.status = 45
                          AND prot.type = 502
                       )
                   OR prot.type = vps.status)) AS "r" WHERE (date >= '2024-11-26T00:00:00.000Z') AND (date < '2025-05-03T00:00:00.000Z') ORDER BY "sorting_day" ASC, "no_time" ASC, "order_number" ASC, "sorting_date" ASC, "lot_id" ASC
    '''
    cur.execute(query)
    rows = cur.fetchall()

    colnames = [desc[0] for desc in cur.description]

    result = []
    for row in rows:
        result.append(dict(zip(colnames, row)))

    cur.close()
    conn.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
