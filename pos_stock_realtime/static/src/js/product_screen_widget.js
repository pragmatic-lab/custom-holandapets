odoo.define('pos_stock_realtime.product_screen_widget', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');

    screens.PaymentScreenWidget.include({
        finalize_validation: function () {
            if (this.pos.config.show_qty_available) {
                this.sub_qty();
            }
            this._super();
        },
        sub_qty: function () {
            var self = this;
            var order = this.pos.get_order();
            var orderlines = order.get_orderlines();
            var sub_qty_by_product_id = {};
            var ids = [];
            orderlines.forEach(function (line) {
                if (!sub_qty_by_product_id[line.product.id]) {
                    sub_qty_by_product_id[line.product.id] = line.quantity;
                    ids.push(line.product.id);
                } else {
                    sub_qty_by_product_id[line.product.id] += line.quantity;
                }
            });

            ids.forEach(function (id) {
                if (self.pos.db.qty_by_product_id[id] !== false && self.pos.db.qty_by_product_id[id] !== undefined) {
                    self.pos.db.qty_by_product_id[id] -= sub_qty_by_product_id[id];
                }
            });
        }
    });
});