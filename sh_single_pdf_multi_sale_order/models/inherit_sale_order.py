# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models

class MergeOrders(models.Model):
    _inherit = 'sale.order'

    def merge_sale_order_report(self,active_so_ids):
        product_list = []
        product_dic = {}
        for data in active_so_ids:
            if data.order_line:
                for record in data.order_line:
                    if record.product_id.x_studio_hss_code_2:                
                        if record.product_id.x_studio_hss_code_2 not in product_list:
                            product_list.append(record.product_id.x_studio_hss_code_2)
                            some_dic = {
                                "hss_code" : record.product_id.x_studio_hss_code_2.x_name,
                                "desc" : record.product_id.x_studio_hss_description,
                                'quantity' : record.product_uom_qty,
                                'weight' : record.product_id.weight * record.product_uom_qty,
                                'volume' : record.product_id.volume * record.product_uom_qty,
                                'price' : record.price_subtotal,
                            }
                            product_dic[record.product_id.x_studio_hss_code_2] = some_dic
                        else:                        
                            for key,value in product_dic.items():
                                if key == record.product_id.x_studio_hss_code_2:
                                    value['quantity'] = value['quantity'] + record.product_uom_qty
                                    value['weight'] = value['weight'] + (record.product_id.weight * record.product_uom_qty)
                                    value['volume'] = value['volume'] + (record.product_id.volume * record.product_uom_qty)
                                    value['price'] = value['price'] + record.price_subtotal
                      
        return product_dic
