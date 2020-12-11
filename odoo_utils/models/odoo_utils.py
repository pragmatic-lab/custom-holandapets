import pytz
import json
import logging
from datetime import datetime, timedelta

from odoo import models, api, fields, tools
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.osv.orm import transfer_modifiers_to_node
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_is_zero
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OdooUtils(models.AbstractModel):
    _name = 'odoo.utils'
    _description = 'Utilidades Varias'
    
    #http://stackoverflow.com/a/7029418
    @api.model
    def get_week_of_month(self, date):
        month = date.month
        week = 0
        while date.month == month:
            week += 1
            date -= timedelta(days=7)
        return week
    
    @api.model
    def get_weeks(self, date_start, date_end):
        res = []
        date_end_aux = datetime.strptime(date_end,DF)
        date_aux = datetime.strptime(date_start, DF)
        while True:
            week = self.get_week_of_month(date_aux)
            start_week_date = None
            end_week_date = None
            week_aux = date_aux
            while True:
                if week_aux.isoweekday() == 1:
                    start_week_date = week_aux
                    break
                week_aux -= timedelta(days=1)
            week_aux = date_aux
            while True:
                if week_aux.isoweekday() == 7:
                    end_week_date = week_aux
                    break
                week_aux += timedelta(days=1)
            data = {'name': 'Semana %s del %s al %s' % (week, start_week_date.strftime(DF), end_week_date.strftime(DF)),
                    'start_date': start_week_date,
                    'end_date': end_week_date,
                    }
            res.append(data)
            date_aux += timedelta(days=7)
            if date_aux.month != date_end_aux.month:
                if end_week_date.month != date_end_aux.month:
                    res.remove(data)
                break
        return res
        
    @api.model
    def get_selection_item(self, model, field, value=None):
        """
        Obtener el valor de un campo selection
        @param model: str, nombre del modelo
        @param field: str, nombre del campo selection
        @param value: str, optional, valor del campo selection del cual obtener el string
        @return: str, la representacion del campo selection que se muestra al usuario
        """
        try:
            field_val = value
            if field_val:
                return dict(self.env[model].fields_get(allfields=[field], attributes=['selection'])[field]['selection'])[field_val]
            return ''
        except Exception:
            return ''
        
    @api.model
    def replace_character_especial(self, string_to_reeplace, list_characters=[]):
        """
        Reemplaza caracteres por otros caracteres especificados en la lista
        @param string_to_reeplace:  string a la cual reemplazar caracteres
        @param list_characters:  Lista de tuplas con dos elementos(elemento uno el caracter a reemplazar, elemento dos caracter que reemplazara al elemento uno)
        @return: string con los caracteres reemplazados
        """
        if not list_characters:
            list_characters=[('á','a'),('à','a'),('ä','a'),('â','a'),('Á','A'),('À','A'),('Ä','A'),('Â','A'),
                             ('é','e'),('è','e'),('ë','e'),('ê','e'),('É','E'),('È','E'),('Ë','E'),('Ê','E'),
                             ('í','i'),('ì','i'),('ï','i'),('î','i'),('Í','I'),('Ì','I'),('Ï','I'),('Î','I'),
                             ('ó','o'),('ò','o'),('ö','o'),('ô','o'),('Ó','O'),('Ò','O'),('Ö','O'),('Ô','O'),
                             ('ú','u'),('ù','u'),('ü','u'),('û','u'),('Ú','U'),('Ù','U'),('Ü','U'),('Û','U'),
                             ('ñ','n'),('Ñ','N'),('/','-'), ('&','Y'),('º','')]
        for character in list_characters:
            string_to_reeplace= string_to_reeplace.replace(character[0],character[1])
        return string_to_reeplace
    
    @api.model
    def _change_time_zone(self, date, from_zone=None, to_zone=None):
        """
        Cambiar la informacion de zona horaria a la fecha
        En caso de no pasar la zona horaria destino, tomar la zona horaria del usuario
        @param date: Object datetime to convert according timezone in format '%Y-%m-%d %H:%M:%S'
        @return: datetime according timezone
        """
        fields_model = self.env['ir.fields.converter']
        if not from_zone:
            #get timezone from user
            from_zone = fields_model._input_tz()
        #get UTC per Default
        if not to_zone:
            to_zone = pytz.UTC
        #si no hay informacion de zona horaria, establecer la zona horaria
        if not date.tzinfo:
            date = from_zone.localize(date)
        date = date.astimezone(to_zone)
        return date
    
    @api.model
    def show_wizard(self, model, id_xml, name, target='new', nodestroy=True):
        obj_model = self.env['ir.model.data']
        model_data_recs = obj_model.search([('model','=','ir.ui.view'),('name','=',id_xml)])
        resource_id = model_data_recs.res_id
        ctx = self.env.context.copy()
        return {'name': name,
                'view_type': 'form',
                'view_mode': 'form',
                'nodestroy': nodestroy, 
                'res_model': model,
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target': target,
                'context': ctx,
                }

    @api.model
    def show_message(self, message, title='Mensaje'):
        message_model = self.env['wizard.messages']
        new_wizard = message_model.create({'message': message})
        return self.show_view(name=title, model='wizard.messages', id_xml='ecua_utilidades.wizard_messages_form_view', res_id=new_wizard.id)
        
    @api.model
    def show_view(self, name, model, id_xml, res_id=None, view_mode='tree,form', nodestroy=True, target='new'):
        view = self.env.ref(id_xml)
        view_mode = view.type
        ctx = self.env.context.copy()
        ctx.update({'active_model': model})
        res = {'name': name,
               'view_type': 'form',
               'view_mode': view_mode,
               'view_id': view.id,
               'res_model': model,
               'res_id': res_id,
               'nodestroy': nodestroy,
               'target': target,
               'type': 'ir.actions.act_window',
               'context': ctx,
               }
        return res
    
    @api.model
    def show_action(self, id_xml, domain=None):
        if domain is None:
            domain = []
        #pasar el domain a una lista en caso de no serlo
        if not isinstance(domain, list):
            try:
                domain = list(domain)
            except:
                domain = []
        action_rec = self.env.ref(id_xml)
        result = action_rec.read()[0]
        domain_action = []
        if result['domain']:
            domain_action = eval(result['domain'])
        domain.extend(domain_action)
        result['domain'] = domain
        ctx = self.env.context.copy()
        try:
            ctx = eval(result.get('context', {}))
            ctx.update(self.env.context)
        except:
            pass
        result['context'] = ctx
        return result
    
    @api.model
    def get_field_value(self, fields_required, object_list, raise_error=False):
        """
        devuelve el valor del(os) campo(s) solicitado(s), buscando en la lista de modelos dados
        si son varios campos requeridos, todos deben estar configurados en el mismo objeto
        si falta un campo, seguir evaluando los demas objetos
        @param field_required: lista de campos solicitado
        @param object_list: lista de objetos browse_record, el orden de la lista, determina la prioridad de busqueda
        @return: dict (k,v), (field, value), diccionario con los valores solicitados
        """
        translation_model = self.env['ir.translation']
        def get_objects_name():
            object_name = []
            for o in object_list:
                object_name.append('%s %s' % (translation_model._get_source('', 'model', self.env.context.get('lang','es_EC'), o._description), o.display_name))
            return " o ".join(object_name)
        
        def build_msj():
            #todos los campos deben estar en todos los objetos
            #asi que tomar cualquier objeto para obtener la informacion de los campos
            res_model = self.env[object_list[0]._name]
            fields_info = res_model.fields_get(fields_required)
            field_name = ""
            for f in fields_info:
                #si es un campo de unidad de medida no mostrarlo en el label
                if fields_info.get(f,{}).get('type','') == 'many2one' and fields_info.get(f,{}).get('relation','') == 'uom.uom':
                    continue
                field_name += "%s, " % fields_info.get(f,{}).get('string',f)
            msj = _("You must be configure Fields: %s In: %s") % (field_name, get_objects_name())
            return msj
        fields_invalid = []
        res = {}
        #pasar un valor por defecto
        for f in fields_required:
            res[f] = None
        if not fields_required:
            return res
        if not object_list:
            object_list = []
        done_all = False
        #recorrer cada objeto para encontrar los campos requeridos
        for obj in object_list:
            res_model = self.env[obj._name]
            for f in fields_required:
                if not f in res_model._fields:
                    if not f in fields_invalid:
                        fields_invalid.append(f)
                    continue
                #si el campo si pertenece al modelo
                #pero en un modelo anterior no estaba
                #sacarlo de la lista de campos no encontrados
                else:
                    if f in fields_invalid:
                        fields_invalid.remove(f)
                res[f] = obj[f]
                #los campos deben estan configurados todos en el mismo objeto
                #en caso de faltar un campo, seguir buscando en los demas objetos
            done = True
            for f2 in res:
                if not f2 in res_model._fields:
                    if not f2 in fields_invalid:
                        fields_invalid.append(f)
                    done = False
                    continue
                #si el campo si pertenece al modelo
                #pero en un modelo anterior no estaba
                #sacarlo de la lista de campos no encontrados
                else:
                    if f2 in fields_invalid:
                        fields_invalid.remove(f2)
                col_info = res_model._fields[f2]
                #FIX: si es un campo boolean, y esta en False, se debe aceptar como configurado
                if col_info.type == 'boolean':
                    continue
                if col_info.type == 'float':
                    #si es campo float y tiene 0, solo si es el ultimo objeto, darlo como configuracion valida
                    if obj != object_list[-1] and res[f2] == 0.0:
                        #por un campo que no este configurado
                        #pasar al siguiente objeto
                        done = False
                        break
                    if res[f2] < 0.0:
                        #por un campo que no este configurado
                        #pasar al siguiente objeto
                        done = False
                        break        
                elif not res[f2]:
                    #por un campo que no este configurado
                    #pasar al siguiente objeto
                    done = False
                    break
            if done:
                done_all = True
                break
        #si hay campos que no existen en el modelo
        #mostrar error
        if fields_invalid:
            raise UserError(_("Fields: %s not found in Objects : %s") % (",".join(fields_invalid), get_objects_name()))
        if not done_all and raise_error:
            raise UserError(build_msj())
        return res
    
    @api.model
    def copy_per_sql(self, res_model, alias, res_id, clause_from="", clause_where=""):
        """
        Copiar un registro por SQL
        considerando los campos m2o(FOREING KEY a nivel de BD) que no sean null, 
        ya que darian problemas al hacer el INSERT INTO en columnas NOT NULL
        @param res_model: str, nombre del modelo(ejm. product.product)
        @param res_id: int, id del registro a copiar
        @return: int, id del nuevo registro copiado, False en caso de no poder copiar el registro
        """
        if isinstance(res_id, (list, tuple)):
            res_id = res_id[0]
        res_model = self.env[res_model]
        if not res_model:
            return False
        record = res_model.browse(res_id)
        sql_fields = []
        has_value = False
        for f in res_model._fields:
            has_value = False
#             #campos funcionales o related que no se almacenan en la BD
#             if isinstance(res_model._fields[f], (fields.function, fields.one2many, fields.many2many)) and not res_model._columns[f]._classic_write:
#                 continue
            #campos que no se almacenan en la BD
            if not res_model._fields[f]._classic_write:
                continue
            #campos floar o boolean siempre debo copiar
            if res_model._fields[f].type in ('float','boolean'):
                has_value = True
            elif record[f]:
                has_value = True
            #solo si el campo tiene algun valor, copiarlo
            #esto para controlar los FOREING KEY NOT NULL
            if has_value: 
                sql_fields.append(f)
        #agregar campos de log, ya que no siempre estan explicitos
        for f in ('create_uid','create_date','write_uid','write_date'):
            if f not in sql_fields:
                sql_fields.append(f)
        self.env.cr.execute("SELECT nextval('%s')" % (res_model._sequence))
        new_id = self.env.cr.fetchone()[0]
        SQL = "SELECT " +  ",".join([alias + "." + f for f in sql_fields]) + \
              " FROM " + res_model._table + " " + alias + " " + clause_from +\
              "  WHERE " + alias + ".id = "  + str(res_id) + " " + clause_where
        self.env.cr.execute(SQL)
        res = self.env.cr.fetchone()
        up0 = ",%s" * len(sql_fields)
        SQL = "INSERT INTO " + res_model._table + " (id," + ",".join(sql_fields) + ") VALUES (" + str(new_id) + up0 + ")"
        self.env.cr.execute(SQL, tuple(res))
        return new_id 
    
    @api.model
    def vals_to_upper(self, model, vals, fields_skip=None):
        """
        Pasar los valores de un dict a mayusculas, puede ser llamado desde create o write
        """
        if fields_skip is None:
            fields_skip = []
        res_model = self.env[model]
        if res_model:
            for f,v in vals.items():
                if f in fields_skip:
                    continue
                if f in res_model._fields and res_model._fields[f].type in ('text','char') and isinstance(v, str):
                    vals.update({f: v.upper()})
        return vals
    
    @api.model
    def GetSQLProductStock(self, product_ids, location_ids, lot_ids=None, date_from=None, date_to=None, group_by_location=False, fields_select=None):
        field_data = {
            'qty_available': 'COALESCE(SUM(report.qty_available),0) AS ',
            'price_unit': """CASE WHEN COALESCE(SUM(report.qty_available),0) > 0 THEN COALESCE(SUM(report.valuation),0) / COALESCE(SUM(report.qty_available),0)
                            ELSE 0 END AS """,
            'valuation': 'COALESCE(SUM(report.valuation),0) AS ',
            'virtual_available': 'COALESCE(SUM(report.qty_available),0) + COALESCE(SUM(report.incoming),0) - COALESCE(SUM(report.outgoing),0) AS ',
            'incoming_qty': 'SUM(incoming) AS ',
            'outgoing_qty': 'SUM(outgoing) AS ',
                        
        }
        if not fields_select:
            fields_select = [('qty_available', 'qty_available'),
                            ('price_unit', 'price_unit'),
                            ('valuation', 'valuation'),
                            ('virtual_available', 'virtual_available'),
                            ('incoming_qty', 'incoming_qty'),
                            ('outgoing_qty', 'outgoing_qty'),
                            ]
        if not lot_ids:
            lot_ids = []
        extra_where = ""
        extra_select = []
        params = {'product_ids': tuple(product_ids),
                  'location_ids': tuple(location_ids),
                  }
        if date_from:
            extra_where += " AND sm.date >= %(date_from)s"
            params['date_from'] = date_from
        if date_to:
            extra_where += " AND sm.date < %(date_to)s"
            params['date_to'] = date_to
        if lot_ids:
            extra_where += " AND sm.restrict_lot_id IN %(lot_ids)s"
            params['lot_ids'] = tuple(lot_ids)
        for field, alias in fields_select:
            if field in field_data:
                extra_select.append(field_data[field] + alias)
        if extra_select:
            extra_select =  ",".join(extra_select)
            extra_select = "," + extra_select
        else:
            extra_select = ""
        SQL = """
            SELECT P.id AS product_id
                """ + extra_select + """
            FROM product_product P
                LEFT JOIN 
                    (SELECT 
                        product_id, 
                        SUM(qty) AS qty_available,
                        SUM(valuation) AS valuation,
                        0 AS incoming, 0 AS outgoing
                        FROM 
                            (
                            SELECT 
                                sm.product_id AS product_id,
                                SUM(sm.product_qty) AS qty,
                                SUM(sm.product_qty * sm.price_unit) AS valuation
                            FROM stock_move sm
                            WHERE 
                                sm.product_id IN %(product_ids)s
                                AND sm.location_id NOT IN %(location_ids)s 
                                AND sm.location_dest_id IN %(location_ids)s
                                AND sm.state = 'done' """+extra_where+"""
                            GROUP BY product_id
                            UNION ALL
                            SELECT
                                sm.product_id AS product_id,
                                -SUM(sm.product_qty) AS qty,
                                -SUM(sm.product_qty * sm.price_unit) AS valuation 
                            FROM stock_move sm
                            WHERE sm.product_id IN %(product_ids)s
                                AND sm.location_id IN %(location_ids)s
                                AND sm.location_dest_id NOT IN %(location_ids)s
                                AND sm.state = 'done' """+extra_where+"""
                            GROUP BY product_id
                    ) AS product_stock_available 
                    GROUP BY product_id
                    UNION ALL
                        SELECT 
                            prod AS product_id, 
                            0 as qty_available,
                            0 as valuation, 
                            SUM(stock_in_out_data.in) AS incoming,
                            SUM(stock_in_out_data.out) AS outgoing
                        FROM
                            (SELECT 
                                product_id AS prod,
                                SUM(product_qty) AS in,
                                0 as out
                            FROM stock_move sm
                            WHERE 
                                product_id IN %(product_ids)s
                                AND sm.location_id NOT IN %(location_ids)s 
                                AND sm.location_dest_id IN %(location_ids)s
                                AND sm.state IN ('confirmed', 'waiting', 'assigned') """+extra_where+"""
                                GROUP BY product_id
                            UNION
                            SELECT
                                product_id AS prod, 
                                0 AS in, 
                                SUM(product_qty) AS out 
                            FROM stock_move sm
                            WHERE product_id IN %(product_ids)s
                                AND sm.location_id IN %(location_ids)s
                                AND sm.location_dest_id NOT IN %(location_ids)s
                                AND sm.state IN ('confirmed', 'waiting', 'assigned') """+extra_where+"""
                            GROUP BY product_id
                            ) AS stock_in_out_data
                            GROUP BY prod
                ) report ON (P.id = report.product_id)
            WHERE P.id IN %(product_ids)s
            GROUP BY P.id 
            ORDER BY P.id
        """
        return SQL, params
    
    @api.model
    def GetProductStock(self, product_ids, location_ids, lot_ids=None, date_from=None, date_to=None, group_by_location=False):
        SQL, params = self.GetSQLProductStock(product_ids, location_ids, lot_ids, date_from, date_to, group_by_location)
        self.env.cr.execute(SQL, params)
        return self.env.cr.dictfetchall()
    
    @api.model
    def GetSQLProductStockMove(self, product_ids, location_ids, lot_ids=None, date_from=None, date_to=None):
        if not lot_ids:
            lot_ids = []
        extra_where = ""
        params = {'product_ids': tuple(product_ids),
                  'location_ids': tuple(location_ids),
                  }
        if date_from:
            extra_where += " AND sm.date >= %(date_from)s"
            params['date_from'] = date_from
        if date_to:
            extra_where += " AND sm.date < %(date_to)s"
            params['date_to'] = date_to
        if lot_ids:
            extra_where += " AND sm.restrict_lot_id IN %(lot_ids)s"
            params['lot_ids'] = tuple(lot_ids)
        SQL = """
            SELECT P.id AS product_id, 
                sm.name AS move_name,
                sm.date,
                sm.location_id,
                sm.location_dest_id,
                sm.state,
                COALESCE(sm.product_qty,0) AS product_qty,
                COALESCE(sm.price_unit,0) AS price_unit
            FROM product_product P
                INNER JOIN 
                    (SELECT 
                        sm.product_id,
                        sm.name,
                        TO_CHAR(sm.date AT TIME ZONE 'UTC', 'YYYY-MM-dd HH24:MI:SS') AS date,
                        sm.location_id,
                        sm.location_dest_id,
                        sm.state,
                        COALESCE(sm.product_qty,0) AS product_qty,
                        COALESCE(sm.price_unit,0) AS price_unit
                    FROM stock_move sm
                    WHERE sm.product_id IN %(product_ids)s
                        AND sm.location_id NOT IN %(location_ids)s 
                        AND sm.location_dest_id IN %(location_ids)s
                        """+extra_where+"""
                    UNION ALL
                    SELECT
                        sm.product_id,
                        sm.name,
                        TO_CHAR(sm.date AT TIME ZONE 'UTC', 'YYYY-MM-dd HH24:MI:SS') AS date,
                        sm.location_id,
                        sm.location_dest_id,
                        sm.state,
                        COALESCE(sm.product_qty,0) AS product_qty,
                        COALESCE(sm.price_unit,0) AS price_unit 
                    FROM stock_move sm
                    WHERE sm.product_id IN %(product_ids)s
                        AND sm.location_id IN %(location_ids)s
                        AND sm.location_dest_id NOT IN %(location_ids)s
                        """+extra_where+"""
            ) sm ON (P.id = sm.product_id)
            WHERE P.id IN %(product_ids)s
            ORDER BY P.id, sm.date
        """
        return SQL, params
    
    @api.model
    def GetSQLProductAttributes(self, fields_aditionals=None, company_id=None):
        if not fields_aditionals:
            fields_aditionals = []
        if not company_id:
            company_id = self.env.user.company_id.id
        extra_fields = ", ".join(fields_aditionals)
        params = {'company_id': company_id}
        SQL = """
            SELECT p.id, p.default_code, p.barcode,
                t.name,
                t.categ_id AS category,
                t.list_price,
                ARRAY_TO_STRING(ARRAY(SELECT CONCAT(pa.name, ':', atr.name)
                                        FROM product_attribute_value_product_product_rel rel
                                            LEFT JOIN product_attribute_value AS atr ON (atr.id=rel.product_attribute_value_id)
                                            LEFT JOIN product_attribute pa ON (pa.id = atr.attribute_id)
                                        WHERE rel.product_product_id=p.id
                                    ),',') as attributos,
                COALESCE(prop.value, 0) AS precio_costo
                 """ + ((", " + extra_fields) if extra_fields else "") + """
            FROM product_product AS p
                INNER JOIN product_template t ON (t.id=p.product_tmpl_id)
                LEFT JOIN (
                    SELECT CAST(SUBSTRING(res_id FROM 17 FOR 10) AS integer) AS product_id,
                        value_float AS value, company_id
                    FROM ir_property 
                    WHERE name = 'standard_price'
                ) AS prop ON (p.id = prop.product_id AND prop.company_id = %(company_id)s)
        """
        return SQL, params
    
    @api.model
    def GetSQLProductData(self, product_ids=None, company_id=None):
        if not company_id:
            company_id = self.env.user.company_id.id
        params = {'company_id': company_id}
        SQL = """
            SELECT p.id AS product_id, a.id AS attribute_id, v.name AS value
            FROM product_product AS p
                LEFT JOIN product_attribute_value_product_product_rel m2m ON m2m.product_product_id = p.id
                LEFT JOIN product_attribute_value v ON v.id = m2m.product_attribute_value_id
                LEFT JOIN product_attribute a ON a.id = v.attribute_id
                WHERE a.id IS NOT NULL
        """
        if product_ids:
            SQL += " AND p.id IN %(product_ids)s"
            params['product_ids'] = tuple(product_ids)
        return SQL, params
    
    @api.model
    def _check_availability(self, move_datas):
        """
        asigna el lote de produccion al movimiento de stock
        considerando la cantidad a requerir
        """
        ctx = self.env.context.copy()
        ctx_uom = self.env.context.copy()
        location_model = self.env['stock.location']
        product_model = self.env['product.product']
        lot_model = self.env['stock.production.lot']
        quant_model = self.env['stock.quant']
        uom_model = self.env['uom.uom']
        digits_precision = dp.get_precision('Product Unit of Measure')(self.env.cr)
        digits_precision = digits_precision and digits_precision[1] or 2
        qty_asignned_lot = {}
        lot_no_availables = {}
        message = ''
        for move in move_datas:
            if move.get('type_product') == 'semi':
                continue
            #si el movimiento ya tiene lote de produccion no hacer la asignacion de lote nuevamente
            if move.get('restrict_lot_id',False):
                continue
            #buscar los quants que no esten reservados y que tengan lotes de produccion
            domain = [('qty', '>', 0.0), ('reservation_id','=', False), ('lot_id','!=', False)]
            #no considerar los lotes ya asignados aqui
            if lot_no_availables:
                domain.append(('lot_id', 'not in', tuple(lot_no_availables.keys())))
            location_stock = location_model.browse(move['location_stock_id'])
            product = product_model.browse(move['product_id'])
            uom = uom_model.browse(move['product_uom'])
            move.update({'product': product,
                         'uom': uom,
                         'location_stock': location_stock,
                         })
            product_qty = move['product_uom_qty']
            #calcular disponibilidad en la UdM por defecto del producto
            product_qty = uom_model.with_context(ctx_uom)._compute_qty(move['product_uom'], product_qty, product.uom_id.id) 
            quants = quant_model.quants_get_prefered_domain(location_stock, product, product_qty, domain=domain)
            lot_ids = []
            for quant, quant_qty in quants:
                if quant and quant.lot_id.id not in lot_ids:
                    lot_ids.append(quant.lot_id.id)
            ctx['location'] = move['location_stock_id']
            for lot in lot_model.with_context(ctx).browse(lot_ids):
                ctx_uom['product_id_comp_uom'] = lot.product_id.id
                #si el lote no esta disponible porque ya no hay cantidad disponible(acumulando las cantidades que los componentes necesitan).
                #pasar al siguiente lote
                if lot.id in lot_no_availables:
                    continue
                #pasar la cantidad del lote(que esta en la UdM de referecia) a la UdM del movimiento
                stock_available = uom_model.with_context(ctx_uom)._compute_qty(lot.product_id.uom_id.id, lot.stock_available, move.get('product_uom'))
                #si no hay suficiente cantidad en el lote pasar al siguiente lote
                if stock_available <= 0: 
                    continue
                qty_accumulated = qty_asignned_lot.get(lot.id,0)
                qty_total= qty_accumulated + move.get('product_uom_qty')
                if stock_available >= qty_total:
                    move.update({'restrict_lot_id': lot.id})
                    qty_asignned_lot[lot.id] = qty_total
                    #FIX, si he asignado toda la cantidad de ese lote, marcarlo como no disponible
                    if stock_available == qty_asignned_lot[lot.id]:
                        lot_no_availables[lot.id]= True
                    break
                #asignar la cantidad disponible del lote a la linea y crear una nueva linea con la cantidad restante
                else:
                    qty_remaining = (stock_available - qty_accumulated)
                    qty_asignned_lot[lot.id] = qty_accumulated + qty_remaining
                    #si la cantidad restante no es cero, crear otra linea con lo restante
                    if not float_is_zero(move.get('product_uom_qty') - qty_remaining, precision_digits=digits_precision):
                        new_line = move.copy()
                        new_line['product_uom_qty'] = move.get('product_uom_qty') - qty_remaining
                        move_datas.append(new_line)
                    move.update({'restrict_lot_id': lot.id,
                                 'product_uom_qty': qty_remaining,
                                 })
                    lot_no_availables[lot.id]= True
                    break
        #obtener las lineas que no tienen lote de produccion
        not_lot= {}
        with_lot= {}
        for move in move_datas:
            product = move.pop('product', False)
            uom = move.pop('uom', False)
            location_stock = move.pop('location_stock', False)
            if move.get('type_product') == 'semi':
                continue
            key = (product, uom, location_stock)
            if not move.get('restrict_lot_id') :
                #acumular las cantidades de los productos que no tienen lote de produccion
                not_lot[key] = not_lot.get(key, 0) + move.get('product_uom_qty')  
            else:
                #acumular las cantidades de los productos que si tienen lote de produccion
                with_lot[key] = with_lot.get(key, 0) + move.get('product_uom_qty')
        for key, qty_remaining in not_lot.items():
            name_product = key[0].display_name
            name_uom = key[1].name
            name_location = key[2].display_name
            qty_assigned = with_lot.get(key, 0)
            message += 'No hay stock disponible en la ubicación "%s" para el producto "%s son necesarias %s %s. hay disponibles %s %s". \n'\
                         'Por favor asegurese que los movimientos tengan lote de producción.' \
                         % (name_location, name_product, qty_remaining + qty_assigned, name_uom, qty_assigned, name_uom)
        #no lanzar excepcion si asi se pasa por context
        if message and not self.env.context.get('no_raise_exception',False):
            raise UserError(message)
        return move_datas
    
    @api.model
    def get_stock_initial(self, product_id, all_location_ids, date):
        params = {
            'location_ids': tuple(all_location_ids),
            'product_id': product_id,
            'start_date': date
        }
        self.env.cr.execute('''
            SELECT sm.product_id AS product_id,
                SUM(sm.product_qty) AS qty_in
            FROM stock_move sm
                INNER JOIN product_product pp ON pp.id = sm.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE sm.location_dest_id IN %(location_ids)s
                AND sm.location_id NOT IN %(location_ids)s
                AND sm.state = 'done'
                AND product_id = %(product_id)s
                AND sm.date < %(start_date)s
            GROUP BY product_id
        ''', params)
        data = self.env.cr.dictfetchone()
        start_qty_in = data and data.get('qty_in', 0.0) or 0.0
        self.env.cr.execute('''
            SELECT sm.product_id AS product_id,
                SUM(sm.product_qty) AS qty_out
            FROM stock_move sm
                INNER JOIN product_product pp ON pp.id = sm.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE sm.location_dest_id NOT IN %(location_ids)s
                AND sm.location_id IN %(location_ids)s
                AND sm.state = 'done'
                AND product_id = %(product_id)s
                AND sm.date < %(start_date)s
            GROUP BY product_id
        ''', params)
        data = self.env.cr.dictfetchone()
        start_qty_out = data and data.get('qty_out', 0.0) or 0.0
        return start_qty_in, start_qty_out
    
    @api.model
    def find_node(self, node_root, node_find, node_type="field", node_attribute="name"):
        nodes = node_root.xpath("//%s[@%s='%s']" % (node_type, node_attribute, node_find))
        return nodes 
    
    @api.model
    def set_node_modifiers(self, nodes, node_modifiers):
        for node in nodes:
            #tomar los atributos actuales y solo modificar los nuevos
            modifiers_curr = node.get('modifiers', {})
            try:
                modifiers_curr = json.loads(modifiers_curr)
            except:
                modifiers_curr = {}
            modifiers_curr.update(node_modifiers)
            transfer_modifiers_to_node(modifiers_curr, node)
        return nodes
    
    @api.model
    def set_node(self, nodes, attribute, value):
        for node in nodes:
            node.set(attribute, value)
        return nodes
    
    @api.model
    def find_set_node(self, node_root, node_find, node_modifiers, node_type="field", node_attribute="name"):
        nodes = self.find_node(node_root, node_find, node_type, node_attribute)
        return self.set_node_modifiers(nodes, node_modifiers)
    
    @api.model
    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    @api.model
    def _insert_into_mogrify(self, table_name, values):
        """
        Mejora inserccion de registros en BD, siempre y cuando los valores a ingresar cumplan lo siguiente
        Mismos campos y en mismo orden
        @param values: list(dict) lista de diccionario con los valores a insertar en la BD
        """
        if values:
            #todos deben tener los mismos campos, tomar el primero
            fields_name = values[0].keys()
            #pasar los valores como tuplas, deben tener el mismo orden que los nombres de los campos
            values_insert = list(map(tuple, [v.values() for v in values]))
            SQL = self.env.cr.mogrify("INSERT INTO " + table_name + " (" + ", ".join(fields_name) + ") values " + ','.join(["%s"] * len(values)), values_insert)
            self.env.cr.execute(SQL)
        return True
    
    @api.model
    def _ensure_zero_values(self, dict_data):
        if not dict_data: dict_data = {}
        for key in dict_data.keys():
            if not dict_data.get(key): dict_data[key] = 0.0
        return dict_data
    
    @api.model
    def float_to_str_time(self, value):
        if value:
            if isinstance(value, (float, int)):
                value = float(value)
                value = str(value)
            if len(value) >= 3:
                asplit = value.split('.')
                return '%02d:%02d' % (int(asplit[0]) , int(float('0.' + asplit[1]) *  60))
        return ''
    
    @api.model
    def compute_total_documents(self, total_lines, max_lines):
        document_number, remaining = divmod(total_lines, max_lines)
        if remaining > 0:
            document_number += 1
        return document_number
    
    def get_ensure_id(self, recordset):
        #Devolver el ID del registro, hay problemas en los onchange, que no se pasa el id
        #sino un NewID, pero el id de BD se guarda en la variable _origin.id
        #sin embargo en algunos casos la variable _origin no se pasa
        #asi que tratar de tomar el id correctamente
        record_id = recordset.id
        if hasattr(recordset, '_origin') and recordset._origin.id:
            record_id = recordset._origin.id
        if isinstance(record_id, models.NewId):
            record_id = False
        return record_id
    
    def convert_field_boolean_property(self, model, field):
        table = model.replace('.', '_')
        company_id = self.env.user.company_id.id
        self.env.cr.execute("""SELECT 1
                        FROM information_schema.columns
                       WHERE table_name = %s
                         AND column_name = %s
                   """, (table, field))
        if not self.env.cr.fetchone():
            return
        self.env.cr.execute("SELECT id FROM ir_model_fields WHERE model=%s AND name=%s", (model, field))
        [fields_id] = self.env.cr.fetchone()
    
        self.env.cr.execute("""
            INSERT INTO ir_property(name, type, fields_id, company_id, res_id, value_integer)
            SELECT %(field)s, 'boolean', %(fields_id)s, %(company_id)s, CONCAT('{model},', id), 1
              FROM {table} t
             WHERE {field} = true
               AND NOT EXISTS(SELECT 1
                                FROM ir_property
                               WHERE fields_id=%(fields_id)s
                                 AND company_id=%(company_id)s
                                 AND res_id=CONCAT('{model},', t.id))
        """.format(**locals()), locals())
        self.env.cr.execute('ALTER TABLE "{0}" DROP COLUMN "{1}" CASCADE'.format(table, field))

    def convert_field_char_property(self, model, field):
        table = model.replace('.', '_')
        company_id = self.env.user.company_id.id
        self.env.cr.execute("""SELECT 1
                        FROM information_schema.columns
                       WHERE table_name = %s
                         AND column_name = %s
                   """, (table, field))
        if not self.env.cr.fetchone():
            return
        self.env.cr.execute("SELECT id FROM ir_model_fields WHERE model=%s AND name=%s", (model, field))
        [fields_id] = self.env.cr.fetchone()
        self.env.cr.execute("""
            INSERT INTO ir_property(name, type, fields_id, company_id, res_id, value_text)
            SELECT %(field)s, 'char', %(fields_id)s, %(company_id)s, CONCAT('{model},', id),
                   {field}
              FROM {table} t
             WHERE {field} IS NOT NULL
               AND NOT EXISTS(SELECT 1
                                FROM ir_property
                               WHERE fields_id=%(fields_id)s
                                 AND company_id=%(company_id)s
                                 AND res_id=CONCAT('{model},', t.id))
        """.format(**locals()), locals())
        self.env.cr.execute('ALTER TABLE "{0}" DROP COLUMN "{1}" CASCADE'.format(table, field))
        
    def convert_field_float_property(self, model, field):
        table = model.replace('.', '_')
        company_id = self.env.user.company_id.id
        self.env.cr.execute("""SELECT 1
                        FROM information_schema.columns
                       WHERE table_name = %s
                         AND column_name = %s
                   """, (table, field))
        if not self.env.cr.fetchone():
            return
        self.env.cr.execute("SELECT id FROM ir_model_fields WHERE model=%s AND name=%s", (model, field))
        [fields_id] = self.env.cr.fetchone()
        self.env.cr.execute("""
            INSERT INTO ir_property(name, type, fields_id, company_id, res_id, value_float)
            SELECT %(field)s, 'float', %(fields_id)s, %(company_id)s, CONCAT('{model},', id), {field}
              FROM {table} t
             WHERE {field} IS NOT NULL
               AND NOT EXISTS(SELECT 1
                                FROM ir_property
                               WHERE fields_id=%(fields_id)s
                                 AND company_id=%(company_id)s
                                 AND res_id=CONCAT('{model},', t.id))
        """.format(**locals()), locals())
        self.env.cr.execute('ALTER TABLE "{0}" DROP COLUMN "{1}" CASCADE'.format(table, field))
        
    def convert_field_m2o_property(self, model, field, target_model):
        table = model.replace('.', '_')
        company_id = self.env.user.company_id.id
        self.env.cr.execute("""SELECT 1
                        FROM information_schema.columns
                       WHERE table_name = %s
                         AND column_name = %s
                   """, (table, field))
        if not self.env.cr.fetchone():
            return
        self.env.cr.execute("SELECT id FROM ir_model_fields WHERE model=%s AND name=%s", (model, field))
        [fields_id] = self.env.cr.fetchone()
        self.env.cr.execute("""
            INSERT INTO ir_property(name, type, fields_id, company_id, res_id, value_reference)
            SELECT %(field)s, 'many2one', %(fields_id)s, %(company_id)s, CONCAT('{model},', id),
                   CONCAT('{target_model},', {field})
              FROM {table} t
             WHERE {field} IS NOT NULL
               AND NOT EXISTS(SELECT 1
                                FROM ir_property
                               WHERE fields_id=%(fields_id)s
                                 AND company_id=%(company_id)s
                                 AND res_id=CONCAT('{model},', t.id))
        """.format(**locals()), locals())
        self.env.cr.execute('ALTER TABLE "{0}" DROP COLUMN "{1}" CASCADE'.format(table, field))
                