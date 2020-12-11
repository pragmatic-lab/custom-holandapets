odoo.define('pos_base.screens', function (require) {
"use strict";
var screens = require('point_of_sale.screens');
var core = require('web.core');
var QWeb = core.qweb;

screens.ActionpadWidget.include({
    renderElement: function() {
        var self = this;
        this._super();
        this.$('.pay').unbind();
        this.$('.pay').click(function () {
            self.action_show_payment_screen();
        });
        this.$('.set-customer').click(function(){
            self.gui.show_screen('clientlist');
        });
    },
    action_show_payment_screen: function() {
    	return this.payment();
    },
    payment: function () {
        // This method has been added to encapsulate the original widget's logic
        // just to make code more clean and readable
        var self = this;
        var order = self.pos.get_order();
            var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                return line.has_valid_product_lot();
            });
            if (has_valid_product_lot) {
                self.gui.show_screen('payment');
            }else{
                self.gui.show_popup('confirm',{
                    'title': _t('Empty Serial/Lot Number'),
                    'body':  _t('One or more product(s) required serial/lot number.'),
                    confirm: function(){
                        self.gui.show_screen('payment');
                    },
                });
            }
    },
});

});
