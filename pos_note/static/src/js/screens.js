odoo.define('pos_note.screens', function(require) {

	var core = require('web.core');
	var _t = core._t;

	var screens = require('point_of_sale.screens');

	screens.OrderWidget.include({
		action_refresh_order_buttons : function(buttons, selected_order) {
			if (buttons.button_order_note) {
				if (selected_order['note']) {
					buttons.button_order_note.highlight(false);
					var $note = this.el.querySelector('.order-note-content');
					if ($note) {
						$note.textContent = selected_order.get_note();
					}
				} else {
					buttons.button_order_note.highlight(true);
					var $note = this.el.querySelector('.order-note-content');
					if ($note) {
						$note.textContent = "";
					}
				}

			}
			if (buttons.button_order_line_note) {
				if (selected_order.selected_orderline
						&& selected_order.selected_orderline['note']) {
					buttons.button_order_line_note.highlight(false);
				} else {
					buttons.button_order_line_note.highlight(true);
				}

			}
			return this._super(buttons, selected_order);
		}
	});
	
	screens.PaymentScreenWidget.include({
		renderElement: function () {
            var self = this;
            this._super();
            this.$('.js_add_note').click(function () { // Button add Note
            	var order = self.pos.get_order();
                if (order) {
                    self.hide();
                    self.gui.show_popup('textarea', {
                        title: _t('Add Order Note'),
                        value: order.get_note(),
                        confirm: function (note) {
                            order.set_note(note);
                            order.trigger('change', order);
                            self.show();
                            self.renderElement();
                        },
                        cancel: function () {
                            self.show();
                            self.renderElement();
                        }
                    });
                }
            });
		}
	});

	var ButtonOrderNote = screens.ActionButtonWidget.extend({
		template : 'button_order_note',
		button_click : function() {
			var order = this.pos.get_order();
			if (order) {
				this.gui.show_popup('textarea', {
					title : _t('Add Note'),
					value : order.get_note(),
					confirm : function(note) {
						order.set_note(note);
						order.trigger('change', order);
					}
				});
			}
		}
	});

	var ButtonOrderLineNote = screens.ActionButtonWidget.extend({
		template : 'button_order_line_note',
		button_click : function() {
			var line = this.pos.get_order().get_selected_orderline();
			if (line) {
				this.gui.show_popup('textarea', {
					title : _t('Add Note'),
					value : line.get_note(),
					confirm : function(note) {
						line.set_note(note);
					}
				});
			} else {
				this.pos.gui.show_popup('error', {
					title : _t('Warning'),
					body : _t('Please select line the first')
				})
			}
		}
	});

	screens.define_action_button({
		'name' : 'button_order_note',
		'widget' : ButtonOrderNote,
		'condition' : function() {
			return this.pos.config.enable_order_note == true;
		}
	});

	screens.define_action_button({
		'name' : 'button_order_line_note',
		'widget' : ButtonOrderLineNote,
		'condition' : function() {
			return this.pos.config.enable_order_line_note == true;
		}
	});

	return {
		ButtonOrderNote : ButtonOrderNote,
		ButtonOrderLineNote : ButtonOrderLineNote,
	};
});