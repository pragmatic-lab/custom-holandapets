/* Copyright 2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html). */
odoo.define('pos_orders_history_return.models', function (require) {
    "use strict";

    var models = require('pos_orders_history.models');
    
    models.load_fields("res.users", ['allow_credit_note']);

    var _super_pos_model = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_returned_orders_by_pos_reference: function(reference) {
            var all_orders = this.db.pos_orders_history;
            return all_orders.filter(function(order){
                return order.returned_order && order.pos_reference === reference;
            });
        },
        get_qty_returned_orders_by_pos_reference: function(reference) {
        	var self = this;
        	var returned_orders = this.get_returned_orders_by_pos_reference(reference);
            var qty_returned_data = {};
            if (returned_orders && returned_orders.length) {
                returned_orders.forEach(function(o) {
                    o.lines.forEach(function(line_id) {
                        var line = self.db.line_by_id[line_id];
                        var product = self.db.get_product_by_id(line.product_id[0]);
                        if (line.line_origin_id){
                        	if (line.line_origin_id[0] in qty_returned_data){
                            	qty_returned_data[line.line_origin_id[0]] += line.qty;
                            } else {
                            	qty_returned_data[line.line_origin_id[0]] = line.qty;
                            }	
                        }
                    });
                });
            }
            return qty_returned_data;
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        add_product: function(product, options) {
            var self = this;
        	options = options || {};
            if (this.get_mode() === "return") {
                var current_return_qty = this.get_current_product_return_qty(product, product.line_origin_id);
                var quantity = 1;
                if(typeof options.quantity !== 'undefined') {
                    quantity = options.quantity;
                }
                var max_return_qty = 0;
                if (product.line_origin_id){
                	var line_original = self.pos.db.line_by_id[product.line_origin_id] || {};
                	var qty_returned_data = self.pos.get_qty_returned_orders_by_pos_reference(self.name);
                	max_return_qty = (line_original.qty || 0) + (qty_returned_data[line_original.id] || 0);
                	options.discount = line_original.discount || 0;
                	if (line_original.price_unit){
                		options.price = line_original.price_unit;
                	}
                	if (line_original.discount_value){
                		options.extras = {};
                		options.extras.discount_value = line_original.discount_value;
                	}
                }
                if (current_return_qty + quantity <= max_return_qty) {
                    _super_order.add_product.call(this, product, options);
                    this.change_return_product_limit(product, product.line_origin_id);
                }
            } else {
                _super_order.add_product.apply(this, arguments);
            }
        },
        get_current_product_return_qty: function(product, line_origin_id) {
            var orderlines = this.get_orderlines();
            var product_orderlines = orderlines.filter(function(line) {
                return line.product.id === product.id && line.line_origin_id === line_origin_id;
            });
            var qty = 0;
            product_orderlines.forEach(function(line){
                qty += line.quantity;
            });
            if (qty < 0) {
                qty = -qty;
            }
            return qty;
        },
        change_return_product_limit: function(product, line_origin_id) {
        	var self = this;
            if (this.get_mode() === "return_without_receipt") {
                return;
            }
            var el = $('article[data-product-id="'+product.id+'"] .max-return-qty');
            var max_return_qty = 0;
            if (line_origin_id){
            	el = $('article[data-product-id="'+product.id+'"][data-line_origin_id="'+line_origin_id+'"] .max-return-qty')
            	var line_original = self.pos.db.line_by_id[line_origin_id] || {};
            	var qty_returned_data = self.pos.get_qty_returned_orders_by_pos_reference(self.name);
            	max_return_qty = (line_original.qty || 0) + (qty_returned_data[line_original.id] || 0);
            }
            var qty = this.get_current_product_return_qty(product, line_origin_id);
            el.html(max_return_qty - qty);
        },
        export_as_JSON: function() {
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.return_lines = this.return_lines;
            data.origin_order_id = this.origin_order_id || false;
            data.return_data_aditional = this.return_data_aditional || {};
            return data;
        },
        export_for_printing : function() {
			var receipt = _super_order.export_for_printing.call(this);
			receipt.origin_order_id = this.origin_order_id || false;
			receipt.return_data_aditional = this.return_data_aditional || {};
			return receipt;
		},
        init_from_JSON: function(json) {
            this.return_lines = json.return_lines;
            _super_order.init_from_JSON.call(this, json);
            if (json.origin_order_id) {
				this.origin_order_id = json.origin_order_id;
			}
			if (json.return_data_aditional) {
				this.return_data_aditional = json.return_data_aditional;
			}
        }
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options){
        	if ((options.product || {}).line_origin_id){
            	this.line_origin_id = options.product.line_origin_id;
            }
            _super_orderline.initialize.apply(this, arguments);
            var order = this.pos.get_order();
            if (order && order.get_mode() === "return"){
            	this.price_manually_set = true;
            	if (this.product.old_price && this.product.lst_price !== this.product.old_price) {
	                this.set_unit_price(this.product.old_price);
            	}
            }
        },
        export_as_JSON: function() {
            var data = _super_orderline.export_as_JSON.apply(this, arguments);
            data.line_origin_id = this.line_origin_id;
            return data;
        },
        init_from_JSON: function(json) {
            this.line_origin_id = json.line_origin_id;
            _super_orderline.init_from_JSON.call(this, json);
        },
        can_be_merged_with: function (orderline) {
        	var self = this;
        	var can_be_merge = false;
        	if (orderline.line_origin_id !== this.line_origin_id) {
        		can_be_merge = false;
            } else {
            	can_be_merge = _super_orderline.can_be_merged_with.apply(this, arguments);
            	if (orderline.line_origin_id){
            		// cuando no se puede hacer merge pero es xq la linea de venta original tiene un precio de venta diferente al del producto
            		// pero al hacer devolucion, se pasa el precio de la linea, se debe poder hacer merge
            		var line_original = this.pos.db.line_by_id[orderline.line_origin_id] || {};
        			if(!can_be_merge & this.get_product().id === orderline.get_product().id){
        				if(self.price === line_original.price_unit && self.get_discount() === orderline.get_discount()){
        					can_be_merge = true;
        				}
        			}
            	}
            }
        	return can_be_merge;
        },
        set_quantity: function(quantity, keep_price) {
            var order = this.pos.get_order();
            var old_quantity = String(quantity);
            if (order && order.get_mode() === "return_without_receipt" && quantity !== "remove" && quantity > 0) {
                quantity = -quantity;
                _super_orderline.set_quantity.call(this, quantity, keep_price);
            } else if (order && order.get_mode() === "return" && quantity !== "remove") {
                var current_return_qty = this.order.get_current_product_return_qty(this.product, this.line_origin_id);
                if (this.quantity) {
                    current_return_qty += this.quantity;
                }
                var max_return_qty = 0;
                if (this.line_origin_id){
                	var line_original = this.pos.db.line_by_id[this.line_origin_id] || {};
                	var qty_returned_data = this.pos.get_qty_returned_orders_by_pos_reference(order.name);
                	max_return_qty = (line_original.qty || 0) + (qty_returned_data[line_original.id] || 0);
                }
                if (quantity && current_return_qty + Number(quantity) <= max_return_qty) {
                    if (quantity > 0) {
                        quantity = -quantity;
                    }
                    _super_orderline.set_quantity.call(this, quantity, keep_price);
                    order.change_return_product_limit(this.product, this.line_origin_id);
                } else if (quantity === "") {
                    _super_orderline.set_quantity.call(this, quantity, keep_price);
                    order.change_return_product_limit(this.product, this.line_origin_id);
                }
            } else {
                _super_orderline.set_quantity.call(this, quantity, keep_price);
            }
        }
    });
});
