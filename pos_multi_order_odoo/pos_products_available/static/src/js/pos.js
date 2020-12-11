odoo.define('pos_product_available.PosModel', function(require){
"use strict";


    var models = require('point_of_sale.models');
    var core = require('web.core');

    var _t = core._t;
    var _super_posmodel = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var partner_model = _.find(this.models, function(model){ return model.model === 'product.product'; });
            partner_model.fields.push('qty_available');
            partner_model.domain.push(['qty_available','>',0]);
            return _super_posmodel.initialize.call(this, session, attributes);
        },
        get_product_image_url: function (product) {
            return window.location.origin + '/web/image?model=product.product&field=image_medium&id=' + product.id;
        }
    });

    var PosModelSuper = models.PosModel;

    models.PosModel = models.PosModel.extend({
        refresh_qty_available:function(product){
            var $elem = $("[data-product-id='"+product.id+"'] .qty-tag");
            $elem.html(product.qty_available);
            if (product.qty_available <= 0 && !$elem.hasClass('not-available')){
                $elem.addClass('not-available');
            }
        },
        push_order: function(order, opts){
            var self = this;
            var pushed = PosModelSuper.prototype.push_order.call(this, order, opts);
            if (order){
                order.orderlines.each(function(line){
                    var product = line.get_product();
                    product.qty_available -= line.get_quantity();
                    self.refresh_qty_available(product);
                });
            }
            return pushed;
        },
        push_and_invoice_order: function(order){
            var self = this;
            var invoiced = PosModelSuper.prototype.push_and_invoice_order.call(this, order);

            if (order && order.get_client()){
                if (order.orderlines){
                    order.orderlines.each(function(line){
                        var product = line.get_product();
                        product.qty_available -= line.get_quantity();
                        self.refresh_qty_available(product);
                    });
                } else if (order.orderlines){
                    order.orderlines.each(function(line){
                        var product = line.get_product();
                        product.qty_available -= line.get_quantity();
                        self.refresh_qty_available(product);
                    });
                }
            }

            return invoiced;
        },
    });

    var PosModelOrderline = models.Orderline;

    models.Orderline = models.Orderline.extend({
        set_quantity: function(quantity, keep_price){
            var self = this;
            var quant = parseFloat(quantity) || 0;
            var product = this.get_product();
            if (product.qty_available < quant && product.type != "service") {
                this.pos.gui.show_popup('order_reminder', {
                    max_available: product.qty_available,
                    product_image_url: self.pos.get_product_image_url(self.product),
                    product_name: product.display_name,
                    line: self
                });
                return;
            }
            else {
                return PosModelOrderline.prototype.set_quantity.call(this, quantity, keep_price);
            }
        }
    });

});
