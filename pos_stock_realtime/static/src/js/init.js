odoo.define('pos_stock_realtime.init', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');

    models.load_fields('product.product', ['type']);

    models.load_models([{
        loaded: function (self) {
        this.stock_location_ids = [];

        var done = new $.Deferred();

        if (!self.config.show_qty_available) {
            return done.resolve();
        }

        if (self.config.allow_out_of_stock) {
            self.config.limit_qty = 0;
        }

        if (self.config.location_only) {
            rpc.query({
                model: 'stock.quant',
                method: 'get_qty_available',
                args: [self.shop.id]
            }).then(function (res) {
                self.stock_location_ids = _.uniq(res.map(function (item) {
                    return item.location_id[0];
                }));
                self.compute_qty_in_pos_location(res);
                done.resolve();
            });
        } else {
            var ids = _.keys(self.db.product_by_id).map(function (item) {
                return parseInt(item);
            });

            rpc.query({
                model: 'product.product',
                method: 'read',
                args: [ids, ['qty_available']]
            }).then(function (res) {
                res.forEach(function (product) {
                    self.db.qty_by_product_id[product.id] = product.qty_available;
                });
                self.refresh_qty();
                done.resolve();
            });

            done.resolve();
        }
        return done;
        }
    }],
    {
    after: 'account.journal' // nearly at the end of steps, after stock,location and product step
    });
});