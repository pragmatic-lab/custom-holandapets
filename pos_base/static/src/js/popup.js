odoo.define('pos_base.popup', function (require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var PopupWidget = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');
var field_utils = require('web.field_utils');

PosBaseWidget.include({
	format_date: function(date_str){
		return field_utils.format.date(moment(date_str), {});
    },
    format_datetime: function(date_str){
		var d = new Date(date_str);
		return field_utils.format.datetime(moment(d), {});
    },
	get_label_for_field: function(field_name){
    	return this.$el.find('.popup-label').filter(_.str.sprintf("[for='%s']", field_name));
    },
    validate_fields_aditional: function(){
    	var self = this;
    	var fields_warnings = [];
    	var fields_into_warnings = [];
    	// validar que los campos adicionales para pasar al backend esten llenos
    	// solo para los que tengan class detail-required
    	this.$el.find('.pos-popup-box .field_invalid').removeClass('field_invalid');
    	this.$el.find('.pos-popup-box .detail-required').each(function(idx,el){
    		if (el.type === undefined){
    			return true;
    		}
    		if (el.type === "radio"){
        		if (self.$('input[name=' + el.name + ']:checked').length <= 0){
        			var field_id = el.name.length > 0 ? el.name : el.id;
        			var field_label = field_id;
            		var labels = self.get_label_for_field(field_id);
            		if (labels.length > 0){
            			field_label = labels.text();
            		}
            		$(el).parent().addClass('field_invalid');
            		if (!_.contains(fields_into_warnings, el.name)){
            			fields_into_warnings.push(el.name);
                		fields_warnings.push(_.str.sprintf('<li>%s</li>', _.escape(field_label)));
            		}
        		}
        	} else{
        		if (!el.value){
            		var field_id = el.name.length > 0 ? el.name : el.id;
            		var field_label = field_id;
            		var labels = self.get_label_for_field(field_id);
            		if (labels.length > 0){
            			field_label = labels.text();
            		}
            		$(el).addClass('field_invalid');
            		fields_warnings.push(_.str.sprintf('<li>%s</li>', _.escape(field_label)));
            	}	
        	}
        });
        if (fields_warnings.length > 0){
    		fields_warnings.unshift('<ul>');
    		fields_warnings.push('</ul>');
        	self.chrome.pos_warning("Los Siguientes campos son Invalidos", fields_warnings.join(''));
        }
        return fields_warnings;
    },
    get_fields_aditional: function(){
    	var self = this;
    	var return_data_aditional = {};
    	// tomar los campos adicionales
    	// seran los elementos que tengan class detail-edit
    	this.$el.find('.pos-popup-box .detail-edit').each(function(idx,el){
    		if (el.type === undefined){
    			return true;
    		}
        	var field_id = el.name.length > 0 ? el.name : el.id;
        	if (el.type === "radio"){
        		if (el.checked){
        			return_data_aditional[field_id] = el.value || false;
        		}
        	}else {
        		return_data_aditional[field_id] = el.value || false;
        	}
        });
        return return_data_aditional;
    },
    build_url_backend: function(model, res_id){
    	var url = window.location.origin + _.str.sprintf("/web#id=%(id)s&view_type=form&model=%(model)s", {
    		id: res_id,
    		model: model,
    	});
    	return url
    },
});

});