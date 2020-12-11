odoo.define('pos_base.chrome', function (require) {
"use strict";

var chrome = require('point_of_sale.chrome');

chrome.Chrome.include({
	build_widgets: function () {
		var widget_orders = _.findWhere(this.widgets, {'name': 'order_selector'});
		this.widgets =  _.without(this.widgets, widget_orders);
        this._super();
        if ( !widget_orders.condition || widget_orders.condition.call(this) ) {
            var args = typeof widget_orders.args === 'function' ? widget_orders.args(this) : widget_orders.args;
            var w = new widget_orders.widget(this, args || {});
            w.appendTo(this.$('.buttons_pane'));
            this.widget[widget_orders.name] = w;
        }
    }
});
});