odoo.define('pos_rounding.models', function (require) {
"use strict";

var models = require('point_of_sale.models')
var utils = require('web.utils');

var round_pr = utils.round_precision;
var round_de = utils.round_decimals;

var _super_Order = models.Order.prototype;

models.load_fields("res.country", ["code"]);

models.Order = models.Order.extend({
    set_rounding_status: function(rounding_status) {
        this.rounding_status = rounding_status
    },
    get_rounding_status: function() {
        return this.rounding_status;
    },
    get_change: function(paymentline) {
        if (!paymentline) {
//              var change = this.get_total_paid() - this.get_total_with_tax();
            var change = this.get_total_paid() - this.getNetTotalTaxIncluded();
        } else {
            var change = -this.getNetTotalTaxIncluded();
            var lines  = this.paymentlines.models;
            for (var i = 0; i < lines.length; i++) {
                change += lines[i].get_amount();
                if (lines[i] === paymentline) {
                    break;
                }
            }
        }
        return round_pr(Math.max(0,change), this.pos.currency.rounding);
    },
    get_due: function(paymentline) {
        if (!paymentline) {
            var due = this.getNetTotalTaxIncluded() - this.get_total_paid();
        } else {
            var due = this.getNetTotalTaxIncluded();
            var lines = this.paymentlines.models;
            for (var i = 0; i < lines.length; i++) {
                if (lines[i] === paymentline) {
                    break;
                } else {
                    due -= lines[i].get_amount();
                }
            }
        }
        return round_pr(due, this.pos.currency.rounding);
    },
    getNetTotalTaxIncluded: function() {
    	var total = this.get_total_with_tax();
    	if(this.get_rounding_status()){
    		// para chile debe aplicarse redondeo del banquero
    		// es decir cifras que terminen en 5 se redondean hacia abajo y  no hacia arriba
    		// para los demas casos aplicar redondeo normal(matematico)
    		if (this.pos.company.country.code.toUpperCase() == 'CL'){
    			var remainder = total % this.pos.config.rounding_precision;
                if (remainder < 6) {
                	total = total - remainder;
                }	
    		}
        	if(this.pos.config.enable_rounding && this.pos.config.rounding_option == 'digits'){
        		var value = round_de(total, this.pos.config.rounding_precision)
                return value;
        	}else if(this.pos.config.enable_rounding && this.pos.config.rounding_option == 'points'){
        		var value = round_pr(total, this.pos.config.rounding_precision)
                return value;
        	}
    	}else {
    		return total
    	}
    },
    get_rounding : function(){
        if(this.get_rounding_status()){
            var total = this ? this.get_total_with_tax() : 0;
            var rounding = this ? this.getNetTotalTaxIncluded() - total: 0;
            return rounding;
        }
    },
    export_as_JSON: function() {
        var self = this;
        var new_val = {};
        var orders = _super_Order.export_as_JSON.call(this);
        new_val = {
            rounding: this.get_rounding(),
            is_rounding: this.pos.config.enable_rounding,
            rounding_option: this.pos.config.enable_rounding ? this.pos.config.rounding_option : false,
        }
        $.extend(orders, new_val);
        return orders;
    },
});
});