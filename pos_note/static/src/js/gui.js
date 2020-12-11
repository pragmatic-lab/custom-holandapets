odoo.define('pos_note.gui', function(require) {
	var gui = require('point_of_sale.gui');
	
	gui.Gui.include({
		show_screen: function(screen_name,params,refresh,skip_close_popup) {
			this._super(screen_name,params,refresh,skip_close_popup);
			if (screen_name === "payment" || screen_name === "products"){
				// refrescar la nota de la orden al mostrar la pantalla de pagos
				var order = this.pos.get_order();
				var $note = this.current_screen.el.querySelector('.order-note-content');
				if (order && $note) {
					$note.textContent = order.get_note();
				}
			}
		}
	});
});