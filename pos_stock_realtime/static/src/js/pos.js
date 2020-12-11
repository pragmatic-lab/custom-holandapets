odoo.define('pos_stock_realtime.pos', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    var bus = require('bus.Longpolling');
    var rpc = require('web.rpc');
    var PosModel = models.PosModel;
    var _super_pos = models.PosModel.prototype;
    var Widget = require('web.Widget');


    models.PosModel = PosModel.extend({

        initialize: function (session, attributes) {

            _super_pos.initialize.apply(this, arguments);

            // register listener onNotification of bus_service
            var widget = new Widget(this.chrome);
            widget.call('bus_service', 'onNotification', this, this._onNotification);
            widget.call('bus_service', 'startPolling');
        },
        _onNotification: function (notifications) {
            var stock_quant = notifications.filter(function (item) {
                return item[0][1] === 'pos.stock.channel';
            }).map(function (item) {
                return item[1];
            });
            var flat_stock_quant = _.reduceRight(stock_quant, function (a, b) {
                return a.concat(b)
            }, []);

            this.on_stock_notification(flat_stock_quant);
        },
        on_stock_notification: function (stock_quant) {
            var self = this;
            var product_ids = stock_quant.map(function (item) {
                return item.product_id[0];
            });

            if (this.config && this.config.show_qty_available && product_ids.length > 0) {
                $.when(self.qty_sync(product_ids)).done(function () {
                    self.refresh_qty();
                });
            }
        },
        qty_sync: function (product_ids) {
            var self = this;
            var done = new $.Deferred();
            if (this.config && this.config.show_qty_available && this.config.location_only) {
                rpc.query({
                    model: 'stock.quant',
                    method: 'get_qty_available',
                    args: [false, self.stock_location_ids, product_ids]
                }).then(function (res) {
                    self.recompute_qty_in_pos_location(product_ids, res);
                    done.resolve();
                });

            } else if (this.config && this.config.show_qty_available) {
                rpc.query({
                    model: 'product.product',
                    method: 'read',
                    args: [product_ids, ['qty_available']]
                }).then(function (res) {
                    res.forEach(function (product) {
                        self.db.qty_by_product_id[product.id] = product.qty_available;
                    });
                    done.resolve();
                });
            } else {
                done.resolve();
            }
            return done.promise();
        },
        compute_qty_in_pos_location: function (res) {
            var self = this;
            // self.db.qty_by_product_id = {};
            res.forEach(function (item) {
                var product_id = item.product_id[0];
                if (!self.db.qty_by_product_id[product_id]) {
                    self.db.qty_by_product_id[product_id] = item.quantity;
                } else {
                    self.db.qty_by_product_id[product_id] += item.quantity;
                }
            })
        },
        recompute_qty_in_pos_location: function (product_ids, res) {
            var self = this;
            var res_product_ids = res.map(function (item) {
                return item.product_id[0];
            });

            var out_of_stock_ids = product_ids.filter(function (id) {
                return res_product_ids.indexOf(id) === -1;
            });

            out_of_stock_ids.forEach(function (id) {
                self.db.qty_by_product_id[id] = 0;
            });

            res_product_ids.forEach(function (product_id) {
                self.db.qty_by_product_id[product_id] = false;
            });

            res.forEach(function (item) {
                var product_id = item.product_id[0];

                if (!self.db.qty_by_product_id[product_id]) {
                    self.db.qty_by_product_id[product_id] = item.quantity;
                } else {
                    self.db.qty_by_product_id[product_id] += item.quantity;
                }
            });
        },
        refresh_qty: function () {
            var self = this;
            $('.product-list').find('.qty-tag').each(function () {
                var $product = $(this).parents('.product');
                var id = parseInt($product.attr('data-product-id'));

                var qty = self.db.qty_by_product_id[id];

                if (qty === false) {
                    return;
                }

                if (qty === undefined) {
                    if (self.config.hide_product) {
                        $product.hide();
                        return;
                    } else {
                        qty = 0;
                    }
                }

                $(this).text(qty).show('fast');

                if (qty <= self.config.limit_qty) {
                    $(this).addClass('sold-out');
                    if (!self.config.allow_out_of_stock) {
                        $product.addClass('disable');
                    }
                } else {
                    $(this).removeClass('sold-out');
                    $product.removeClass('disable');
                }
            });
        },
        get_product_image_url: function (product) {
            return window.location.origin + '/web/image?model=product.product&field=image_medium&id=' + product.id;
        }
    });
});