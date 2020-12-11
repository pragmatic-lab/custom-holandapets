odoo.define('pos_stock_realtime.order_line', function (require) {
    "use strict";
    var models = require('point_of_sale.models');

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        set_quantity: function (quantity, keep_price) {
            _super_orderline.set_quantity.call(this, quantity, keep_price);

            if (!this.pos.config.show_qty_available
                || this.pos.config.allow_out_of_stock
                || this.product.type !== 'product') {
                return;
            }


            if (this.pos.gui.current_screen) {
                this.check_reminder();
            }
        },
        check_reminder: function () {
            var self = this;
            var qty_available = this.pos.db.qty_by_product_id[this.product.id];

            var all_product_line = this.order.orderlines.filter(function (orderline) {
                return self.product.id === orderline.product.id;
            });

            if (all_product_line.indexOf(self) === -1) {
                all_product_line.push(self);
            }

            var sum_qty = 0;
            all_product_line.forEach(function (line) {
                sum_qty += line.quantity;
            });

            if (qty_available - sum_qty < this.pos.config.limit_qty) {
                this.pos.gui.show_popup('order_reminder', {
                    max_available: qty_available - sum_qty + self.quantity - this.pos.config.limit_qty,
                    product_image_url: self.pos.get_product_image_url(self.product),
                    product_name: self.product.display_name,
                    line: self
                });
            }
        }
    });

});