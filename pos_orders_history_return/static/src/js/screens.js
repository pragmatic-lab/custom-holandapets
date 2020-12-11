/* Copyright 2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
 * Copyright 2018 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html). */
odoo.define('pos_orders_history_return.screens', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('pos_orders_history.screens');
    var screens_disable_payments = require('pos_disable_payment');
    var models = require('pos_orders_history.models');
    var QWeb = core.qweb;
    var _t = core._t;


    screens.OrdersHistoryScreenWidget.include({
        show: function () {
            var self = this;
            this._super();
            if (this.pos.config.return_orders) {
                this.set_return_action();
                this.pos.bind('change:cashier', this.set_return_action, this);
            }
        },
        set_return_action: function() {
            var self = this;
            var user = this.pos.get_cashier();
        	this.$('.actions.oe_hidden').removeClass('oe_hidden');
            this.$('.button.return').unbind('click');
            this.$('.button.return').click(function (e) {
                var parent = $(this).parents('.order-line');
                var id = parseInt(parent.data('id'));
                self.click_return_order_by_id(id);
            });
            if (!user.allow_credit_note){
            	this.$('.button.return').addClass('oe_hidden');
            }else{
            	this.$('.button.return').removeClass('oe_hidden');
            }
        },
        renderElement: function() {
            this._super();
            var self = this;
            this.$('.button.return-no-receipt').click(function (e) {
                var options = self.prepare_order_for_return();
                if (options === false){
                	return false;
                }
                var order = new models.Order({}, options);
                order.temporary = true;
                order.set_mode("return_without_receipt");
                order.return_lines = [];
                self.set_order_for_return(order);
                self.pos.get('orders').add(order);
                self.pos.gui.back();
                self.pos.set_order(order);
            });
        },
        render_list: function(orders) {
            if (!this.pos.config.show_returned_orders) {
                orders = orders.filter(function(order) {
                    return order.returned_order !== true;
                });
            }
            this._super(orders);
            if (this.pos.config.return_orders) {
                this.set_return_action();
            }
        },
        prepare_order_for_return: function(json) {
        	return _.extend({pos: this.pos}, json ? {json: json} : {});
        },
        set_order_for_return: function(order) {
        	return true;
        },
        generate_unique_id: function(order_id) {
            // Generates a public identification number for the order.
            // The generated number must be unique and sequential. They are made 12 digit long
            // to fit into EAN-13 barcodes, should it be needed

            function zero_pad(num,size){
                var s = ""+num;
                while (s.length < size) {
                    s = "0" + s;
                }
                return s;
            }
            return zero_pad(this.pos.pos_session.id,5) +'-'+
                   zero_pad(this.pos.pos_session.login_number,3) +'-'+
                   zero_pad(order_id,5) +'-'+
                   zero_pad(Math.floor(Math.random()*10000),5);
        },
        click_return_order_by_id: function(id) {
            var self = this;
            var order = self.pos.db.orders_history_by_id[id];
            var uid = order.pos_reference &&
                    order.pos_reference.match(/\d{1,}-\d{1,}-\d{1,}/g) &&
                    order.pos_reference.match(/\d{1,}-\d{1,}-\d{1,}/g)[0];
            var split_sequence_number = uid.split('-');
            var sequence_number = split_sequence_number[split_sequence_number.length - 1];

            var orders = this.pos.get('orders').models;
            var exist_order = orders.find(function(o) {
                return o.uid === uid && Number(o.sequence_number) === Number(sequence_number);
            });

            if (exist_order) {
                this.pos.gui.show_popup('error',{
                    'title': _t('Warning'),
                    'body': _t('You have an unfinished return of the order. Please complete the return of the order and try again.'),
                });
                return false;
            }

            var lines = [];
            order.lines.forEach(function(line_id) {
                lines.push(self.pos.db.line_by_id[line_id]);
            });

            var product_list_widget = this.pos.chrome.screens.products.product_list_widget;

            var products = [];
            var current_products_qty_sum = 0;
            lines.forEach(function(line) {
                var product_original = self.pos.db.get_product_by_id(line.product_id[0]);
                var product = _.clone(product_original);
                if (line.price_unit !== product.lst_price) {
                    product.old_price = Math.abs(line.price_unit);
                }
                product.line_origin_id = line.id;
                current_products_qty_sum +=line.qty;
                products.push(product);
            });

            var returned_orders = this.pos.get_returned_orders_by_pos_reference(order.pos_reference);
            var exist_products_qty_sum = 0;
            returned_orders.forEach(function(o) {
                o.lines.forEach(function(line_id) {
                    var line = self.pos.db.line_by_id[line_id];
                    exist_products_qty_sum +=line.qty;
                });
            });

            if (exist_products_qty_sum + current_products_qty_sum <= 0) {
                this.pos.gui.show_popup('error',{
                    'title': _t('Error'),
                    'body': _t('All products have been returned.'),
                });
                return false;
            }

            var partner_id = order.partner_id || false;

            if (products.length > 0) {
                // create new order for return
                var json = _.extend({}, order);
                json.uid = uid;
                json.sequence_number = Number(sequence_number);
                json.lines = [];
                json.canceled_lines = [];
                json.statement_ids = [];
                json.mode = "return";
                json.return_lines = lines;
                json.pricelist_id = this.pos.default_pricelist.id;
                if (order.table_id) {
                    json.table_id = order.table_id[0];
                }
                var options = self.prepare_order_for_return(json);
                if (options === false){
                	return false;
                }
                order = new models.Order({}, options);
                order.temporary = true;
                order.pos_reprint_reference = self.generate_unique_id(json.id || 1);
                var client = null;
                if (partner_id) {
                    client = this.pos.db.get_partner_by_id(partner_id[0]);
                    if (!client) {
                        console.error('ERROR: trying to load a parner not available in the pos');
                    }
                }
                order.set_client(client);
                self.set_order_for_return(order);
                this.pos.get('orders').add(order);
                this.pos.gui.show_screen('products');
                this.pos.set_order(order);
                product_list_widget.set_product_list(products);
            } else {
                this.pos.gui.show_popup('error', _t('Order Is Empty'));
            }
        },
    });

    screens.ProductCategoriesWidget.include({
        renderElement: function() {
            this._super();
            var self = this;
            var order = this.pos.get_order();
            if (order && (order.get_mode() === "return" || order.get_mode() === "return_without_receipt")) {
                // add exist products
                var products = [];
                var qty_returned_data = self.pos.get_qty_returned_orders_by_pos_reference(order.name);
                // update max qty for current return order
                order.return_lines.forEach(function(line) {
                    var product_original = self.pos.db.get_product_by_id(line.product_id[0]);
                    var product = _.clone(product_original);
                    product.max_return_qty = line.qty + (qty_returned_data[line.id] || 0);
                    if (line.price_unit !== product.lst_price) {
                        product.old_price = Math.abs(line.price_unit);
                    }
                    product.line_origin_id = line.id;
                    products.push(product);
                });
                if (products.length) {
                    this.product_list_widget.set_product_list(products);
                }
            }
        }
    });

    screens.ProductListWidget.include({
    	init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.click_product_handler = function(){
                var product = self.pos.db.get_product_by_id(this.dataset.productId);
                product.line_origin_id = $(this).data('line_origin_id');
                options.click_product_action(product);
            };
    	},
        render_product: function(product){
        	var self = this;
            var order = this.pos.get_order();
            this.return_mode = false;
            if (order && order.get_mode() === "return") {
                this.return_mode = true;
            }
            if (this.return_mode || (!this.return_mode && product.old_price)) {
                var current_pricelist = this._get_active_pricelist();
                var cache_key = this.calculate_cache_key(product, current_pricelist);
                this.product_cache.clear_node(cache_key);
            }

            var cached = this._super(product);

            var el = $(cached).find('.max-return-qty');
            if (el.length) {
                el.remove();
            }
            if (this.return_mode && typeof product.line_origin_id !== 'undefined') {
            	var line_original = self.pos.db.line_by_id[product.line_origin_id] || {};
                var current_return_qty = order.get_current_product_return_qty(product, product.line_origin_id);
                var qty_returned_data = self.pos.get_qty_returned_orders_by_pos_reference(order.name);
                var qty = ((line_original.qty || 0) + (qty_returned_data[line_original.id] || 0)) - current_return_qty;
                $(cached).find('.product-img').append('<div class="max-return-qty">' + qty + '</div>');
            }
            if (this.return_mode) {
                this.product_cache.clear_node(product.id);
            }
            return cached;
        },
    });
    
    screens_disable_payments.NumpadWidget.include({
        init: function () {
            this._super.apply(this, arguments);
            this.pos.bind('change:selectedOrder', this.check_access, this);
        },
        check_access: function () {
            var order = this.pos.get_order();
            if (order && (order.get_mode() === "return" || order.get_mode() === "return_without_receipt")) {
            	this._super.apply(this, arguments);
            	this.$el.find("[data-mode='discount']").addClass('disable');
            	this.$el.find("[data-mode='price']").addClass('disable');
            	this.$el.find('.numpad-minus').addClass('disable');
            }else{
            	this._super.apply(this, arguments);
            }
        },
    });

    return screens;
});
