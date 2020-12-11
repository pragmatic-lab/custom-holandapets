odoo.define('pos_rounding.screens', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var core = require('web.core');

var QWeb = core.qweb;

screens.PaymentScreenWidget.include({
	renderElement: function(){
        var self = this;
		this._super();
        this.$('.rounding').click(function(){
        	self.toggle_rounding_button();
        });
	},
    click_paymentmethods: function(id) {
		// antes de agregar el pago, si es efectivo hacer el redondeo automaticamente
		if (this.pos.config.enable_rounding){
			var self = this;
    		var cashregister = null;
    		var order = this.pos.get_order();
            for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
                if ( this.pos.cashregisters[i].journal_id[0] === id ){
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }
            if (cashregister && cashregister.journal.type == 'cash'){
            	// cuando esta activo, desactivarlo y volver a activarlo para refrescar los calculos de ser necesario
            	// caso contrario solo activarlo
            	if (order.get_rounding_status()){
            		self.toggle_rounding_button();
            		self.toggle_rounding_button();
            	}else{
            		self.toggle_rounding_button();
            	}
            }
		}
		this._super(id);
	},
	click_delete_paymentline: function(cid){
		var self = this;
		this._super(cid);
    	if (self.pos.config.enable_rounding){
        	var order = self.pos.get_order();
        	var has_cash = false;
    		// luego de eliminar el pago,
    		// verificar si no hay un pago con efectivo, quitar el redondeo
			var lines = order.get_paymentlines();
			for ( var i = 0; i < lines.length; i++ ) {
				if (lines[i].cashregister.journal.type == 'cash'){
					has_cash = true;
					break;
				}
			}
			if (!has_cash && order.get_rounding_status()){
            	self.toggle_rounding_button();
    		}
		}
    	return;
    },
    toggle_rounding_button: function(){
        var self = this;
        var order = this.pos.get_order();
        var $rounding_elem = $('#pos-rounding');
        if($rounding_elem.hasClass('fa-toggle-off')){
            $rounding_elem.removeClass('fa-toggle-off');
            $rounding_elem.addClass('fa-toggle-on');
            order.set_rounding_status(true);
        } else if($rounding_elem.hasClass('fa-toggle-on')){
            $rounding_elem.removeClass('fa-toggle-on');
            $rounding_elem.addClass('fa-toggle-off');
            order.set_rounding_status(false);
        }
        this.render_paymentlines();
    },
});
});