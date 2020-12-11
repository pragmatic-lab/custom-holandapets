odoo.define('pos_inherit.pos_receipt', function (require) {
"use strict";

var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');



var screens = require('point_of_sale.screens');
var utils = require('web.utils');
var round_pr = utils.round_precision;
var _super_order = models.Order.prototype;



models.load_fields("product.product", ['warehouse_quantity']);
models.load_fields("res.partner", ['neighborhood']);
models.load_fields("res.partner", ['mobile']);
models.load_fields("res.partner", ['phone']);
models.load_fields("res.partner", ['street2']);
models.load_fields("pos.order", ['name']);
models.load_fields("pos.config", ['partner_id']);

screens.OrderWidget.include({
  update_summary: function(){
        this._super();
    	var self = this;
        var order = this.pos.get_order();

        var total = order ? order.get_total_with_tax() : 0;
        var taxes = order ? total - order.get_total_without_tax() : 0;


        if (this.el.querySelector('.summary .total .subtotal .value')) {
            this.el.querySelector('.summary .total .subtotal .value').textContent = this.format_currency((total - taxes));
        }

    },
});


var __super__ = models.Order.prototype;
var Order = models.Order.extend({
        get_client_mobile: function() {
            var client = this.get('client');
            return client ? client.mobile : "";
        },
        get_client_street2: function() {
            var client = this.get('client');
            return client ? client.street2 : "";
        },
        get_client_neighborhood: function() {
            var client = this.get('client');
            return client ? client.neighborhood : "";
        },
       get_client_state: function() {
            var client = this.get('client');
            console.log('---')
            console.log(client)
            return client ? client.state_id : "";
        },
       get_client_city: function() {
            var client = this.get('client');
            console.log('---')
            console.log(client)
            return client ? client.xcity : "";
        },
    });
    models.Order = Order;


});