odoo.define('pos_stock_realtime.product_list_widget', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var task;


    screens.ProductListWidget.include({
        render_product: function (product) {
            if (this.pos.config.show_qty_available && product.type !== 'product') {
                this.pos.db.qty_by_product_id[product.id] = false;
            }
            return this._super(product);
        },
        renderElement: function () {
            this._super();
            var self = this;
            var done = $.Deferred();
            clearInterval(task);
            task = setTimeout(function () {
                if (self.pos.config.show_qty_available) {
                    self.pos.refresh_qty();
                } else {
                    $(self.el).find('.qty-tag').hide();
                }
                done.resolve();
            }, 100);
            return done;
        }
    });
});