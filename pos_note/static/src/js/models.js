odoo.define('pos_note.models', function(require) {
	var models = require('point_of_sale.models');

	var _super_Order = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize : function() {
			var self = this;
			_super_Order.initialize.apply(this, arguments);
			if (!this.note) {
				this.note = '';
			}
		},
		init_from_JSON : function(json) {
			var res = _super_Order.init_from_JSON.apply(this, arguments);
			if (json.note) {
				this.note = json.note;
			}
		},
		export_as_JSON : function() {
			var json = _super_Order.export_as_JSON.apply(this, arguments);
			json.note = this.get_note();
			return json;
		},
		export_for_printing : function() {
			var receipt = _super_Order.export_for_printing.call(this);
			receipt.note = this.get_note();
			return receipt;
		},
		set_note : function(note) {
			this.note = note;
			this.trigger('change', this);
            this.trigger('new_updates_to_send');
		},
		get_note : function() {
			return this.note || '';
		}
	});

	var _super_OrderLine = models.Orderline.prototype;
	models.Orderline = models.Orderline.extend({
		initialize : function() {
			var self = this;
			_super_OrderLine.initialize.apply(this, arguments);
			if (!this.note) {
				this.note = '';
			}
		},
		init_from_JSON : function(json) {
			var res = _super_OrderLine.init_from_JSON.apply(this, arguments);
			if (json.note) {
				this.note = json.note;
			}
		},
		export_as_JSON : function() {
			var json = _super_OrderLine.export_as_JSON.apply(this, arguments);
			json.note = this.get_note();
			return json;
		},
		export_for_printing : function() {
			var receipt = _super_OrderLine.export_for_printing.call(this);
			receipt.note = this.get_note();
			return receipt;
		},
		set_note : function(note) {
			this.note = note;
			this.trigger('change', this);
		},
		get_note : function() {
			return this.note || '';
		}
	});
});