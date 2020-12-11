odoo.define('generic_pos.screens', function (require) {
"use strict";

var screens = require('point_of_sale.screens');

screens.PaymentScreenWidget.include({
	init: function(parent, options) {
		var self = this;
        this._super(parent, options);
        this.pos.get('orders').bind('add remove change', function () {
			this.renderElement();
		}, this);
	}
});

});
