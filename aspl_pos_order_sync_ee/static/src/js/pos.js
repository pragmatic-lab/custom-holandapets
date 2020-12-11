odoo.define('aspl_pos_order_sync_ee.pos', function (require) {
	"use strict";

	var gui = require('point_of_sale.gui');
	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var chrome = require('point_of_sale.chrome');
	var core = require('web.core');
	var DB = require('point_of_sale.DB');
	var keyboard = require('point_of_sale.keyboard').OnscreenKeyboardWidget;
	var rpc = require('web.rpc');
	var utils = require('web.utils');
	var PopupWidget = require('point_of_sale.popups');
	var bus_service = require('bus.BusService');
    var bus = require('bus.Longpolling');
    var session = require('web.session');

	var QWeb = core.qweb;
	var _t = core._t;
	var round_pr = utils.round_precision;

	models.load_fields("res.users", ['based_on','can_give_discount','can_change_price', 'price_limit', 'discount_limit','pos_user_type','sales_persons']);
	
	screens.ReceiptScreenWidget.include({
		click_next: function() {
	        var res = this._super();
	        if (this.pos.config.enable_reorder && this.pos.user){
	        	this.pos.set_cashier(this.pos.user);
	        	this.chrome.widget.username.renderElement();
	        }
	        return res;
	    },
	});
	
	screens.PaymentScreenWidget.include({
		click_back: function(){
			var self = this;
			var res = self._super();
			if (this.pos.config.enable_reorder && this.pos.user){
	        	this.pos.set_cashier(this.pos.user);
	        	this.chrome.widget.username.renderElement();
	        }
			return res
		},
	});

	var ShowSaleNoteList = screens.ActionButtonWidget.extend({
	    template : 'ShowSaleNoteList',
	    button_click : function() {
	        self = this;
	        self.gui.show_screen('sale_note_list');
	    },
	});

	screens.define_action_button({
	    'name' : 'showsalenotelist',
	    'widget' : ShowSaleNoteList,
	    'condition': function(){
	    	return this.pos.config.enable_reorder && this.pos.config.enable_pedidos_list
	    },
	});

	var SaleNoteListScreenWidget = screens.ScreenWidget.extend({
	    template: 'SaleNoteListScreenWidget',
	    events: {
	    	'click .button.back':  'click_back',
	        'click #print_order': 'click_reprint',
	        'click #edit_order': 'click_edit_order',
	        'click .searchbox .search-clear': 'clear_search',
	        'click #re_order_duplicate': 'click_duplicate_order',
	        'click #delete_draft_sale_note': 'click_delete_sale_note',
	        'click #delete_merge_sale_note': 'click_delete_merge_sale_note',
	        'click .client-line': 'click_order',
	        'click .order-merge': 'click_order_merge',
	        'keyup .searchbox input': 'search_order',
	    },
	    init: function(parent, options){
	    	var self = this;
	        this._super(parent, options);
	        if(this.pos.config.iface_vkeyboard && self.chrome.widget.keyboard){
            	self.chrome.widget.keyboard.connect(this.$('.searchbox input'));
            }
	    },
        click_back: function(){
        	this.gui.show_screen('products');
        },
        click_order: function(event){
        	var self = this;
            var $el = $(event.currentTarget);
            var order_id = parseInt($el.data('id'));
            if (self.pos.db.get_sale_note_merge_by_id(order_id)){
            	$el.removeClass('highlight');
            	self.delete_order_merge(order_id);
            }else{
            	var new_order_to_merge = self.pos.db.get_sale_note_by_id(order_id);
            	if (new_order_to_merge && new_order_to_merge.state == 'draft'){
            		self.pos.db.add_sale_note_merge(new_order_to_merge);
                    var sale_notes = self.pos.db.get_sale_note_merge_list();
                    self.render_list_merge(sale_notes);
                    $el.addClass('highlight');	
            	}
            }
        },
        click_order_merge: function(event){
        	var self = this;
            var $el = $(event.currentTarget);
            self.gui.show_popup('confirm', {
                title: 'Unificar Pedidos',
                body: '¿Esta seguro de unificar los pedidos seleccionados en un solo pedido?.Esto eliminara los pedidos y quedara un solo pedido.',
                confirm: function(){
                	self.action_order_merge();
                }
        	});
        },
        action_order_merge: function(){
        	var self = this;
        	if (this.pos.db.sale_note_list_merge.length > 1){
        		var main_order = this.pos.db.sale_note_list_merge[0];
        		var selectedOrder = this.pos.get_order();
            	selectedOrder.destroy({'reason':'abandon'});
            	var selectedOrder = this.pos.get_order();
            	if (main_order.partner_id && main_order.partner_id[0]) {
                    var partner = self.pos.db.get_partner_by_id(main_order.partner_id[0])
                    if(partner){
                    	selectedOrder.set_client(partner);
                    }
                }
           	 	selectedOrder.set_pos_reference(main_order.pos_reference);
           	 	selectedOrder.set_sequence(main_order.name);
           	 	selectedOrder.set_note(main_order.note);
           	 	if(main_order.salesman_id && main_order.salesman_id[0]){
           	 		selectedOrder.set_salesman_id(main_order.salesman_id[0]);
           	 		selectedOrder.set_salesman_name(main_order.salesman_id[1]);
           	 	}
           	 	this.pos.db.sale_note_list_merge.forEach(function(draft_order) {
	           		if(draft_order.lines.length > 0){
		            	var order_lines = self.get_orderlines_from_order(draft_order.lines);
		            	if(order_lines.length > 0){
			               	_.each(order_lines, function(line){
				    			var product = self.pos.db.get_product_by_id(Number(line.product_id[0]));
			    				selectedOrder.add_product(product, {
			    					quantity: line.qty,
			    					discount: line.discount,
			    					price: line.price_unit,
			    				});
			    				var selected_orderline = selectedOrder.get_selected_orderline();
			    				selected_orderline.set_note(line.note);
				    		})
		            	}
		            }
	           		self.action_delete_sale_note(draft_order.id);
	           	});
                self.gui.show_screen("products");
        	}
        },
        show: function(){
        	var self = this;
	        this._super();
	        if (!self.pos.config.enable_order_merge){
	        	// quitar class para que ocupe toda la pantalla
	        	// al no estar habilitada la opcion de unificar pedidos
	        	$(".left-content-order").removeClass("left-content-order");
	        }
	        this.pos.db.sale_note_list_merge = [];
	        this.pos.db.sale_note_merge_by_id = {};
	        this.reload_orders();
	        this.reload_orders_merge();
        },
        search_order: function(event){
	    	var self = this;
	    	var search_timeout = null;
	    	clearTimeout(search_timeout);
            var query = $(event.currentTarget).val();
            search_timeout = setTimeout(function(){
                self.perform_search(query,event.which === 13);
            },70);
	    },
	    perform_search: function(query, associate_result){
            if(query){
                var orders = this.pos.db.search_salenote_order(query);
//                if ( associate_result && orders.length === 1){
//                    this.gui.back();
//                }
                this.render_list(orders);
            }else{
            	this.reload_orders();
            }
        },
        clear_search: function(){
        	this.reload_orders();
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
        click_delete_sale_note: function(event){
        	var self = this;
        	var order_id = parseInt($(event.currentTarget).data('id'));
        	self.action_delete_sale_note(order_id);
        },
    	action_delete_sale_note: function(order_id){
    		var self = this;
        	var result = self.pos.db.get_sale_note_by_id(order_id);
        	if (result && result.lines.length > 0) {
        		var params = {
    	    		model: 'pos.order',
    	    		method: 'unlink',
    	    		args: [result.id],
    	    	}
        		rpc.query(params, {async: false}).then(function(result){});
        	}
        	var sale_note_to_be_remove = self.pos.db.get_sale_note_by_id(result.id)
        	var sale_note_list = self.pos.db.get_sale_note_list();
        	sale_note_list = _.without(sale_note_list, _.findWhere(sale_note_list, { id: sale_note_to_be_remove.id }));
        	self.render_list(sale_note_list);
        	self.chrome.render_sale_note_order_list(sale_note_list);
        	self.pos.db.add_sale_note(sale_note_list)
        },
        click_delete_merge_sale_note: function(event){
        	var self = this;
        	var order_id = parseInt($(event.currentTarget).data('id'));
        	if (self.pos.db.get_sale_note_merge_by_id(order_id)){
            	self.delete_order_merge(order_id);
            	$(".client-line").filter(function() { 
                    return $(this).data("id") == order_id; 
                }).removeClass("highlight");
            }
        },
        click_reprint: function(event){
        	var self = this;
        	var selectedOrder = this.pos.get_order();
        	var order_id = parseInt($(event.currentTarget).data('id'));
        	selectedOrder.destroy();
        	var selectedOrder = this.pos.get_order();
        	var result = self.pos.db.get_sale_note_by_id(order_id);
        	if (result && result.lines.length > 0) {
        		if (result.partner_id && result.partner_id[0]) {
                    var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                    if(partner){
                    	selectedOrder.set_client(partner);
                    }
                }
        		selectedOrder.set_amount_paid(result.amount_paid);
                selectedOrder.set_amount_return(Math.abs(result.amount_return));
                selectedOrder.set_amount_tax(result.amount_tax);
                selectedOrder.set_amount_total(result.amount_total);
                selectedOrder.set_company_id(result.company_id[1]);
                selectedOrder.set_date_order(result.date_order);
                selectedOrder.set_pos_reference(result.pos_reference);
                selectedOrder.set_user_name(result.user_id && result.user_id[1]);
                if(result.statement_ids.length > 0){
                	self.get_journal_from_order(result.statement_ids);
                }
                if(result.lines.length > 0){
                	var order_lines = self.get_orderlines_from_order(result.lines);
                	if(order_lines.length > 0){
	                	_.each(order_lines, function(line){
		    				var product = self.pos.db.get_product_by_id(Number(line.product_id[0]));
		    				if(product){
		    					selectedOrder.add_product(product, {
		    						quantity: line.qty,
		    						discount: line.discount,
		    						price: line.price_unit,
		    					})
		    				}
		    			})
                	}
                }
                selectedOrder.set_order_id(order_id);
                self.gui.show_screen('receipt');
        	}
        },
        click_duplicate_order: function(event){
        	var self = this;
        	var order_id = parseInt($(event.currentTarget).data('id'));
        	var selectedOrder = this.pos.get_order();
            var result = self.pos.db.get_sale_note_by_id(order_id);
            if(result.lines.length > 0){
            	var order_lines = self.get_orderlines_from_order(result.lines);
            	if(order_lines && order_lines[0]){
            		self.gui.show_popup('duplicate_product_popup',{
            			order_lines:order_lines,
            			'old_order':result,
					});
            	}
            }
        },
        click_edit_order: function(event){
        	var self = this;
        	var order_id = parseInt($(event.currentTarget).data('id'));
            var result = self.pos.db.get_sale_note_by_id(order_id);
            var operation = $(event.currentTarget).data('operation');
            if(result && result.lines.length > 0){
            	if(operation === "edit"){
	            	if(result.state == "paid"){
	            		self.pos.db.notification('danger',_t('This order is paid'));
	                	return
	                }
	                if(result.state == "done"){
	                	self.pos.db.notification('danger',_t('This order is done'));
	                	return
	                }
            	}
            	var selectedOrder = this.pos.get_order();
            	selectedOrder.destroy();
            	var selectedOrder = this.pos.get_order();
            	if (result.partner_id && result.partner_id[0]) {
                    var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                    if(partner){
                    	selectedOrder.set_client(partner);
                    }
                }
            	if($(event.currentTarget).data('operation') !== "reorder"){
	           	 	selectedOrder.set_pos_reference(result.pos_reference);
	           	 	selectedOrder.set_order_id(order_id);
	           	 	selectedOrder.set_sequence(result.name);
	           	 	if(result.salesman_id && result.salesman_id[0]){
	           	 		selectedOrder.set_salesman_id(result.salesman_id[0]);
	           	 		selectedOrder.set_salesman_name(result.salesman_id[1]);
	           	 		selectedOrder.set_note(result.note);
	           	 	}
            	}
	           	if(result.lines.length > 0){
	            	var order_lines = self.get_orderlines_from_order(result.lines);
	            	if(order_lines.length > 0){
		               	_.each(order_lines, function(line){
			    			var product = self.pos.db.get_product_by_id(Number(line.product_id[0]));
		    				selectedOrder.add_product(product, {
		    					quantity: line.qty,
		    					discount: line.discount,
		    					price: line.price_unit,
		    				});
		    				var selected_orderline = selectedOrder.get_selected_orderline();
		    				selected_orderline.set_note(line.note);
			    		})
	            	}
	            }
	           	if(operation === "edit"){
	           		self.gui.show_screen('products');
	           	}else{

/**
	           		return self.gui.select_user({
		                'security':     true,
		                'current_user': self.pos.get_cashier(),
		                'title':      _t('Change Cashier'),
		                'cashier_window': true
		            }).then(function(user){
		                self.pos.set_cashier(user);
		                self.gui.chrome.widget.username.renderElement();
		            }).then(function () {
		            	self.gui.show_screen('payment');
		            });
**/
	           	}
            }
        },
        delete_order_merge: function(order_id){
        	var self = this;
            if (self.pos.db.get_sale_note_merge_by_id(order_id)){
            	delete self.pos.db.sale_note_merge_by_id[order_id];
            	var line_index = _.findIndex(self.pos.db.sale_note_list_merge, function (line) {
                    return line.id === order_id;
                });
                if (line_index  != -1){
                	self.pos.db.sale_note_list_merge.splice(line_index, 1);
                }
            	self.reload_orders_merge();
            }
        },
        render_list: function(orders){
        	var self = this;
        	if(orders){
	            var contents = this.$el[0].querySelector('.sale-note-list-contents');
	            contents.innerHTML = "";
	            var temp = [];
	            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
	                var order    = orders[i];
	                var orderlines = [];
	                order.amount_total = order.amount_total;
	            	var clientline_html = QWeb.render('SaleNotelistLine',{widget: this, order:order, orderlines:orderlines});
	                var clientline = document.createElement('tbody');
	                clientline.innerHTML = clientline_html;
	                clientline = clientline.childNodes[1];
	                if (self.pos.db.get_sale_note_merge_by_id(order.id)){
	                	$(clientline).addClass('highlight');
	                }
	                contents.appendChild(clientline);
	            }
        	}
        },
        render_list_merge: function(orders){
        	var self = this;
        	if(orders && self.pos.config.enable_order_merge){
        		$(".order-merge").toggleClass("oe_hidden", orders.length < 2);
	            var contents = this.$el[0].querySelector('.sale-note-list-contents-merge');
	            contents.innerHTML = "";
	            var temp = [];
	            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
	                var order    = orders[i];
	                var orderlines = [];
	                order.amount_total = order.amount_total;
	            	var clientline_html = QWeb.render('SaleNotelistLineMerge',{widget: this, order: order});
	                var clientline = document.createElement('tbody');
	                clientline.innerHTML = clientline_html;
	                clientline = clientline.childNodes[1];
	                contents.appendChild(clientline);
	            }
        	}
        },
        reload_orders: function(){
        	var self = this;
        	var sale_notes = self.pos.db.get_sale_note_list();
        	self.render_list(sale_notes)
        },
        reload_orders_merge: function(){
        	var self = this;
        	var sale_notes = self.pos.db.get_sale_note_merge_list();
            self.render_list_merge(sale_notes);
        },
        get_journal_from_order: function(statement_ids){
	    	var self = this;
	    	var order = this.pos.get_order();
	    	var params = {
	    		model: 'account.bank.statement.line',
	    		method: 'search_read',
	    		domain: [['id', 'in', statement_ids]],
	    	}
	    	rpc.query(params, {async: false}).then(function(statements){
	    		if(statements.length > 0){
	    			var order_statements = []
	    			_.each(statements, function(statement){
	    				if(statement.amount > 0){
	    					order_statements.push({
	    						amount: statement.amount,
	    						journal: statement.journal_id[1],
	    					})
	    				}
	    			});
	    			order.set_journal(order_statements);
	    		}
	    	}).fail(function(){
            	self.pos.db.notification('danger',"Connection lost");
            });
	    },
	    get_orderlines_from_order: function(line_ids){
	    	var self = this;
	    	var order = this.pos.get_order();
	    	var orderlines = false;
	    	var params = {
	    		model: 'pos.order.line',
	    		method: 'search_read',
	    		domain: [['id', 'in', line_ids]],
	    	}
	    	rpc.query(params, {async: false}).then(function(order_lines){
	    		if(order_lines.length > 0){
	    			orderlines = order_lines;
	    		}
	    	}).fail(function(){
            	self.pos.db.notification('danger',"Connection lost");
            });
	    	return orderlines
	    },
    });
    gui.define_screen({name:'sale_note_list', widget: SaleNoteListScreenWidget});

	var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
    	generateUniqueId_barcode: function() {
            return new Date().getTime();
        },
        set_is_draft_order: function(){
        	this.set('is_draft_order', true);
        },
        get_is_draft_order: function(){
        	return this.get('is_draft_order');
        },
        set_salesman_id: function(salesman_id){
        	this.set('salesman_id',salesman_id);
        },
        get_salesman_id: function(){
        	return this.get('salesman_id');
        },
        set_salesman_name: function(salesman_name){
        	this.set('salesman_name',salesman_name);
        },
        get_salesman_name: function(){
        	return this.get('salesman_name');
        },
        set_sequence:function(sequence){
        	this.set('sequence',sequence);
        },
        get_sequence:function(){
        	return this.get('sequence');
        },
        set_order_id: function(order_id){
            this.set('order_id', order_id);
        },
        get_order_id: function(){
            return this.get('order_id');
        },
        set_amount_paid: function(amount_paid) {
            this.set('amount_paid', amount_paid);
        },
        get_amount_paid: function() {
            return this.get('amount_paid');
        },
        set_amount_return: function(amount_return) {
            this.set('amount_return', amount_return);
        },
        get_amount_return: function() {
            return this.get('amount_return');
        },
        set_amount_tax: function(amount_tax) {
            this.set('amount_tax', amount_tax);
        },
        get_amount_tax: function() {
            return this.get('amount_tax');
        },
        set_amount_total: function(amount_total) {
            this.set('amount_total', amount_total);
        },
        get_amount_total: function() {
            return this.get('amount_total');
        },
        set_company_id: function(company_id) {
            this.set('company_id', company_id);
        },
        get_company_id: function() {
            return this.get('company_id');
        },
        set_date_order: function(date_order) {
            this.set('date_order', date_order);
        },
        get_date_order: function() {
            return this.get('date_order');
        },
        set_pos_reference: function(pos_reference) {
            this.set('pos_reference', pos_reference)
        },
        get_pos_reference: function() {
            return this.get('pos_reference')
        },
        set_user_name: function(user_id) {
            this.set('user_id', user_id);
        },
        get_user_name: function() {
            return this.get('user_id');
        },
        set_journal: function(statement_ids) {
            this.set('statement_ids', statement_ids)
        },
        get_journal: function() {
            return this.get('statement_ids');
        },
        get_change: function(paymentline) {
			if(this.get_order_id()){
				if (!paymentline) {
		        	if(this.get_total_paid() > 0){
		        		var change = this.get_total_paid() - this.get_total_with_tax();
		        	}else{
		        		var change = this.get_amount_return();
		        	}
		        } else {
		            var change = -this.get_total_with_tax(); 
		            var lines  = this.pos.get_order().get_paymentlines();
		            for (var i = 0; i < lines.length; i++) {
		                change += lines[i].get_amount();
		                if (lines[i] === paymentline) {
		                    break;
		                }
		            }
		        }
		        return round_pr(Math.max(0,change), this.pos.currency.rounding);
			} else {
				return _super_Order.get_change.call(this, paymentline);
			}
        },
        export_as_JSON: function() {
        	var new_val = {};
            var orders = _super_Order.export_as_JSON.call(this);
            new_val = {
            	salesman_id: this.get_salesman_id() || this.pos.get_cashier().id,
                old_order_id: this.get_order_id(),
                sequence: this.get_sequence(),
                pos_reference: this.get_pos_reference(),
                is_draft_order: this.get_is_draft_order(),
            }
            $.extend(orders, new_val);
            return orders;
        },
        export_for_printing: function(){
            var orders = _super_Order.export_for_printing.call(this);
            var new_val = {
            	reprint_payment: this.get_journal() || false,
            	ref: this.get_pos_reference() || false,
            	date_order: this.get_date_order() || false,
            };
            $.extend(orders, new_val);
            return orders;
        },
        set_date_order: function(val){
        	this.set('date_order',val)
        },
        get_date_order: function(){
        	return this.get('date_order')
        },
    });

	var _super_posmodel = models.PosModel;
	 models.PosModel = models.PosModel.extend({
		 initialize: function(session, attributes) {
	            var self = this;
	            _super_posmodel.prototype.initialize.call(this, session, attributes);
		},
		set_cashier: function(user){
			var self = this;
			_super_posmodel.prototype.set_cashier.apply(this, arguments);
			if(self.config.enable_reorder){
				var from = moment(new Date()).format('YYYY-MM-DD');
	    		var to = moment(new Date()).format('YYYY-MM-DD');
	        	var domain_sale_note = [];
	        	var user_ids = [];
	    		domain_sale_note.push(['date_order','>=',from]);
	    		domain_sale_note.push(['date_order', '<=', to]);
	            if(self.get_cashier().pos_user_type=="salesman"){
	                    domain_sale_note.push(['salesman_id', '=', self.get_cashier().id]);
	            } else if(self.get_cashier().pos_user_type=="cashier") {
	                if(self.get_cashier().sales_persons && self.get_cashier().sales_persons.length > 0){
	                   var selected_users = self.get_cashier().sales_persons;
	                   _.each(selected_users, function(each_user_id){
	                        user_ids.push(each_user_id)
	                   });
	                   user_ids.push(self.get_cashier().id);
	                   domain_sale_note.push(['salesman_id', 'in', user_ids]);
	                } else {
	                    domain_sale_note.push(['salesman_id', '=', self.get_cashier().id]);
	                }
	            }
	    		var params = {
		    		model: 'pos.order',
		    		method: 'search_read',
		    		domain: domain_sale_note,
		    	}
		    	rpc.query(params, {async: false}).then(function(orders){
		    		self.db.add_sale_note(orders)
		    		self.chrome.render_sale_note_order_list(orders)
		    	});
			}
			if(user.pos_user_type == "cashier"){
				var button_clock = QWeb.render('SaleNoteIconChrome',{widget: self,user:user});
				$('.sale_note_icon_widget').html(button_clock);
				var order_count = self.order_quick_draft_count;
	        	$('.notification-count').show();
	        	$('.draft_order_count').text(order_count);
			} else{
				$('.sale_note_icon_widget').html("");
			}
		},
		get_cashier: function(){
	        // reset the cashier to the current user if session is new
//	        if (this.db.load('pos_session_id') !== this.pos_session.id) {
//	            this.set_cashier(this.user);
//	        }
	        return this.db.get_cashier() || this.get('cashier') || this.user;
	    },
		_save_to_server: function (orders, options) {
			var self = this;
			return _super_posmodel.prototype._save_to_server.apply(this, arguments)
			.done(function(server_ids){
				if(server_ids.length > 0 && self.config.enable_reorder){
					var params = {
						model: 'pos.order',
						method: 'ac_pos_search_read',
						args: [{'domain': [['id','in',server_ids]]}],
					}
					rpc.query(params, {async: false}).then(function(orders){
		                if(orders.length > 0){
		                	_.each(orders,function(order){
		                		var exist_sale_note = _.findWhere(self.db.get_sale_note_list(), {'pos_reference': order.pos_reference})
			                	if(exist_sale_note){
			                    	_.extend(exist_sale_note,order);
			                    } else{
			                    	self.db.sale_note_list.push(order);
			                    }
			                	var new_sale_note = _.sortBy(self.db.get_sale_note_list(), 'id').reverse();
			                    self.db.add_sale_note(new_sale_note)
			                    self.chrome.render_sale_note_order_list(new_sale_note);
		                	})
		                 }
		            });
				}
			});
		},
	});	

	DB.include({
		init: function(options){
        	this._super.apply(this, arguments);
        	this.order_write_date = null;
        	this.order_sorted = [];
        	this.sale_note_list = [];
        	this.sale_note_list_merge = [];
        	this.sale_note_by_id = {};
        	this.sale_note_merge_by_id = {};
        	this.order_search_string = "";
        },
        add_sale_note : function(orders){
            var updated_count = 0;
            var new_write_date = '';
            this.sale_note_list = orders;
            this.sale_note_by_id = {};
            for(var i = 0, len = orders.length; i < len; i++){
                var order = orders[i];
                if (    this.order_write_date &&
                        this.sale_note_by_id[order.id] &&
                        new Date(this.order_write_date).getTime() + 1000 >=
                        new Date(order.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < order.write_date ) {
                    new_write_date  = order.write_date;
                }
                if (!this.sale_note_by_id[order.id]) {
                    this.order_sorted.push(order.id);
                }
                this.sale_note_by_id[order.id] = order;
                updated_count += 1;
            }
            this.order_write_date = new_write_date || this.order_write_date;
            if (updated_count){
            	this.order_search_string = "";
                for (var id in this.sale_note_by_id) {
                    var order = this.sale_note_by_id[id];
                    this.order_search_string += this._order_search_string(order);
                }
            }
            return updated_count;
        },
        get_sale_note_by_id: function(id){
            return this.sale_note_by_id[id];
        },
        get_sale_note_list: function(){
            return this.sale_note_list;
        },
        add_sale_note_merge : function(order){
            if (!this.sale_note_merge_by_id[order.id]) {
                this.sale_note_list_merge.push(order);
            }
            this.sale_note_merge_by_id[order.id] = order;
        },
        get_sale_note_merge_by_id: function(id){
            return this.sale_note_merge_by_id[id];
        },
        get_sale_note_merge_list: function(){
            return this.sale_note_list_merge;
        },
        search_salenote_order: function(query){
            try {
            	query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(/ /g,'.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            var r;
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.order_search_string);
                if(r){
                    var id = Number(r[1]);
                    var order = this.get_sale_note_by_id(id);
                    if (order){
                    	results.push(order);
                    }
                }else{
                    break;
                }
            }
            return results;
        },
        notification: function(type, message){
        	var types = ['success','warning','info', 'danger'];
        	if($.inArray(type.toLowerCase(),types) != -1){
        		$('div.span4').remove();
        		var newMessage = '';
        		message = _t(message);
        		switch(type){
        		case 'success' :
        			newMessage = '<i class="fa fa-check" aria-hidden="true"></i> '+message;
        			break;
        		case 'warning' :
        			newMessage = '<i class="fa fa-exclamation-triangle" aria-hidden="true"></i> '+message;
        			break;
        		case 'info' :
        			newMessage = '<i class="fa fa-info" aria-hidden="true"></i> '+message;
        			break;
        		case 'danger' :
        			newMessage = '<i class="fa fa-ban" aria-hidden="true"></i> '+message;
        			break;
        		}
	        	$('body').append('<div class="span4 pull-right">' +
	                    '<div class="alert alert-'+type+' fade">' +
	                    newMessage+
	                   '</div>'+
	                 '</div>');
        	    $(".alert").removeClass("in").show();
        	    $(".alert").delay(200).addClass("in").fadeOut(5000);
        	}
        },
	});

	screens.ActionpadWidget.include({
        renderElement: function() {
            var self = this;
            this._super();
            var order_count = self.pos.order_quick_draft_count;
        	$('.notification-count').show();
        	$('.draft_order_count').text(order_count);
        },
        show_cashier_window: function() {
            var self = this;
            if (!self.pos.config.enable_reorder){
            	return this._super();
            }else{
            	var order = self.pos.get_order();
            	if(self.pos.get_cashier().pos_user_type=="cashier"){
            		return this._super();
            	} else{
            		var order = self.pos.get_order();
    	        	if(order.is_empty()){
    	        		$('div.order-empty').animate({
    	            	    color: '#FFCCCC',
    	            	}, 1000, 'linear', function() {
    	            	      $(this).css('color','#DDD');
    	            	});
    	        		return
    	        	}
                	self.gui.show_popup('confirm',{
    	                'title': _t('Draft 	Order'),
    	                'body': _t('Do you want to create Draft Order?'),
    	                confirm: function(){
    	                	order.set_is_draft_order();
    	                	self.pos.push_order(order);
    	                	self.gui.show_screen('receipt');
    	                },
    	            });
            	}
            }
        }
	});

	var ReorderProductPopupWidget = PopupWidget.extend({
	    template: 'ReorderProductPopupWidget',
	    show: function(options){
	    	var self = this;
	    	options = options || {};
	    	var lines = options.order_lines || [];
	    	self.order_lines = [];
	    	_.each(lines,function(line){
	        	if(line.product_id[0]){
	        		var product = self.pos.db.get_product_by_id(line.product_id[0]);
	        		if(product && !product.is_dummy_product){
	        			self.order_lines.push(line);
	        		}
	        	}
	        });
	        self.old_order = options.old_order || "";
	        self._super(options);
	        self.renderElement();
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var order = self.pos.get_order();
	    	var selected_ids = [];
	    	var flag = false;
	    	$('.line-selected').map(function(ev){
	    		var id = parseInt($(this).attr('id'));
	    		if(id){
	    			selected_ids.push(id);
	    		}
	    	});
	    	if(selected_ids && selected_ids[0]){
	    		order.destroy();
		    	var order = self.pos.get_order();
	    		selected_ids.map(function(id){
	    			var line = _.find(self.order_lines, function(obj) { return obj.id == id});
	    			var qty = Number($(".popup-product-list tbody").find('tr#'+id+'').find('.js_quantity').val());
	    			if(line && qty > 0){
	    				if(line.product_id && line.product_id[0]){
	    					var product = self.pos.db.get_product_by_id(line.product_id[0]);
	    					if(product){
	    						flag = true;
	    						order.add_product(product, {
			    					quantity: qty,
			    				});
	    					}
	    				}
	    			}
	    		});
	    		if(flag){
	    			if(self.old_order && self.old_order.partner_id && self.old_order.partner_id[0]){
	    				var partner = self.pos.db.get_partner_by_id(self.old_order.partner_id[0]);
	    				if(partner){
	    					order.set_client(partner);
	    				}
	    			}else{
	    				order.set_client(null);
	    			}
	    			self.gui.close_popup();
	    			self.gui.show_screen("products");
	    		}
	    	}
	    },
	    renderElement: function() {
            var self = this;
            this._super();
            $('.js_quantity-reorder').click(function(ev){
	    		ev.preventDefault();
	            var $link = $(ev.currentTarget);
	            var $input = $link.parent().parent().find("input");
	            var min = parseFloat($input.data("min") || 1);
	            var max = parseFloat($input.data("max") || $input.val());
	            var total_qty = parseFloat($input.data("total-qty") || 0);
	            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
	            $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
	            $input.change();
	            return false;
	    	});
            $('.product_line').click(function(event){
            	if($(this).hasClass('line-selected')){
            		$(this).removeClass('line-selected');
            	}else{
            		$(this).addClass('line-selected');
            	}
            });
            $('.remove_line').click(function(){
            	$(this).parent().remove();
            	if($('.product_line').length == 0){
            		self.gui.close_popup();
            	}
            });
    	},
	});
	gui.define_popup({name:'duplicate_product_popup', widget: ReorderProductPopupWidget});

	gui.Gui.include({
        authentication_pin: function(password) {
            var self = this;
            var ret = new $.Deferred();
            var flag = false;
            self.show_popup('password',{
                'title': _t('Password ?'),
                confirm: function(pw) {
                    _.each(password, function(pass) {
                        if (pw === pass) {
                            flag = true;
                        }
                    });
                    if(flag){
                        ret.resolve();
                    } else {
                        self.show_popup('error',_t('Incorrect Password'));
                        ret.reject()
                    }
                },
            });
            return ret;
        },
    });

	screens.OrderWidget.include({
		set_value: function(val) {
		    var self = this;
	    	var order = this.pos.get_order();
	    	if(this.pos.config.enable_operation_restrict){
		    	if (order.get_selected_orderline()) {
		            var mode = this.numpad_state.get('mode');
		            var cashier = this.pos.get_cashier() || false;
		            if( mode === 'quantity'){
		                order.get_selected_orderline().set_quantity(val);
		            }else if( mode === 'discount'){
		            	if(cashier && cashier.can_give_discount){
		            		if(val <= cashier.discount_limit || cashier.discount_limit < 1){
		            			order.get_selected_orderline().set_discount(val);
		            			if(val == ''){
		            				this.numpad_state.change_mode = true
		            			}
		            		} else {
		            		    if(cashier.based_on == 'barcode'){
		            			    this.gui.show_popup('ManagerAuthenticationPopup', { val: val });
		            			}
		            			else{
		            			    var user_detail = {} ,password = [];
                                     _.each(self.pos.users, function(value) {
                                        user_detail[value.id] = value;
                                        password.push(value.pos_security_pin)
                                    });
		            			    var res = self.gui.authentication_pin(password).then(function(){
                                        self.pos.get_order().get_selected_orderline().set_discount(val);
				    				    self.gui.close_popup();
                                    });
		            			}
		            		}
		            	} else {
		            		alert(_t('You don\'t have access to give discount.'));
		            	}
		            }else if( mode === 'price'){
		            	if(cashier && cashier.can_change_price){
		            		order.get_selected_orderline().set_unit_price(val);
		            	} else {
		            		alert(_t('You don\'t have access to change Price.'));
		            	}
		            }
		    	}
	    	} else {
	    		this._super(val)
	    	}
	    },
	});

	var ManagerAuthenticationPopup = PopupWidget.extend({
	    template: 'ManagerAuthenticationPopup',
	    show: function(options){
	    	var self = this;
	    	this.value = options.val || 0;
	    	options = options || {};
	        this._super(options);
	        this.renderElement();
	        $('#manager_barcode').focus();
	        $('#manager_barcode').keypress(function(e){
	        	if(e.which === 13){
	        		self.click_confirm();
	        	}
	        });
	    },
	    click_confirm: function(){
	    	var self = this;
	    	var barcode_input = $('#manager_barcode').val();
	    	var manager_ids;
	    	if(barcode_input){
		    	if(!$.isEmptyObject(self.pos.config.pos_managers_ids)){
		    		var result_find = _.find(self.pos.users, function (o) {
		    			return o.barcode === barcode_input;
		    		});
		    		if(result_find && !$.isEmptyObject(result_find)){
		    			if($.inArray(result_find.id, self.pos.config.pos_managers_ids) != -1){
		    				if(result_find.can_give_discount){
		    					if(self.value <= result_find.discount_limit || result_find.discount_limit < 1){
				    				self.pos.get_order().get_selected_orderline().set_discount(self.value);
				    				this.gui.close_popup();
		    					} else {
		    						alert(_t('out of your discount limit.'));
		    					}
		    				} else {
		    					alert(_t(result_find.name + ' does not have right to give discount.'));
		    				}
		    			} else {
		    				alert(_t('Not a Manager.'));
			    		}
		    		} else {
		    			alert(_t('No result found'));
		    			$('#manager_barcode').val('');
		    			$('#manager_barcode').focus();
		    		}
		    	} else{
		    		alert(_t('Manager not found for this user.'))
		    	}
	    	}else{
	    		alert(_t('Please enter barcode.'));
	    		$('#manager_barcode').focus();
	    	}
	    },
	});
	gui.define_popup({name:'ManagerAuthenticationPopup', widget: ManagerAuthenticationPopup});

	chrome.Chrome.include({
		events: {
            "click #sale_note_chrome": "sale_note_chrome",
            "click #close_draggable_panal" :"close_draggable_panal",
            'click #quick_delete_draft_order' : "quick_delete_draft_order",
            'click #pay_quick_order' : "pay_quick_draft_order",
		},
		build_widgets:function(){
            var self = this;
            this._super();
            self.call('bus_service', 'updateOption','sale.note',session.uid);
            self.call('bus_service', 'onNotification', self, self._onNotification);
            self.call('bus_service', 'startPolling');
		},
		_onNotification: function(notifications){
			var self = this;
			for (var notif of notifications) {
				if (notif[1] && notif[1].cancelled_sale_note){
					var previous_sale_note = self.pos.db.get_sale_note_list();
	    			self.pos.db.notification('danger',_t(notif[1].cancelled_sale_note[0].display_name + ' order has been deleted'));
	    			previous_sale_note = previous_sale_note.filter(function(obj){
	    				return obj.id !== notif[1].cancelled_sale_note[0].id;
	    			});
	    			self.pos.db.add_sale_note(previous_sale_note);
	    			if(self.chrome.screens.sale_note_list){
	    				self.chrome.screens.sale_note_list.render_list(previous_sale_note);
	    			}
	    			self.chrome.render_sale_note_order_list(previous_sale_note);
	    		} else if(notif[1] && notif[1].new_pos_order){
	    			var previous_sale_note = self.pos.db.get_sale_note_list();
	    			if(notif[1].new_pos_order[0].state == "paid"){
	    				self.pos.db.notification('success',_t(notif[1].new_pos_order[0].display_name + ' order has been paid.'));
	    			} else{
	    				self.pos.db.notification('success',_t(notif[1].new_pos_order[0].display_name + ' order has been created.'));
	    			}
	    			previous_sale_note.push(notif[1].new_pos_order[0]);
	    			var obj = {};
	    			for ( var i=0, len=previous_sale_note.length; i < len; i++ ){
	    				obj[previous_sale_note[i]['id']] = previous_sale_note[i];
	    			}
	    			previous_sale_note = new Array();
	    			for ( var key in obj ){
	    				previous_sale_note.push(obj[key]);
	    			}
	    			previous_sale_note.sort(function(a, b) {
	    				return b.id - a.id;
	    			});
	    			self.pos.db.add_sale_note(previous_sale_note)
	    			if(self && self.chrome && self.chrome.screens && self.chrome.screens.sale_note_list){
	    				self.chrome.screens.sale_note_list.render_list(previous_sale_note);
	    			}
	    			self.chrome.render_sale_note_order_list(previous_sale_note);
	    		}
	    	}
		},
		pay_quick_draft_order: function(event){
			var self = this;
        	var order_id = parseInt($(event.currentTarget).data('id'));
            var result = self.pos.db.get_sale_note_by_id(order_id);
            if(result && result.lines.length > 0){
            	var selectedOrder = this.pos.get_order();
            	selectedOrder.destroy();
            	var selectedOrder = this.pos.get_order();
            	if (result.partner_id && result.partner_id[0]) {
                    var partner = self.pos.db.get_partner_by_id(result.partner_id[0])
                    if(partner){
                    	selectedOrder.set_client(partner);
                    }
                }
           	 	selectedOrder.set_pos_reference(result.pos_reference);
           	 	selectedOrder.set_order_id(order_id);
           	 	selectedOrder.set_sequence(result.name);
           	 	selectedOrder.set_note(result.note);
           	 	if(result.salesman_id && result.salesman_id[0]){
           	 		selectedOrder.set_salesman_id(result.salesman_id[0]);
           	 	selectedOrder.set_salesman_name(result.salesman_id[1]);
           	 	}
	           	if(result.lines.length > 0){
	            	var order_lines = self.screens.sale_note_list.get_orderlines_from_order(result.lines);
	            	if(order_lines.length > 0){
		               	_.each(order_lines, function(line){
			    			var product = self.pos.db.get_product_by_id(Number(line.product_id[0]));
		    				selectedOrder.add_product(product, {
		    					quantity: line.qty,
		    					discount: line.discount,
		    					price: line.price_unit,
		    				});
		    				var selected_orderline = selectedOrder.get_selected_orderline();
		    				selected_orderline.set_note(line.note);
			    		})
	            	}
	            }
	           	self.close_draggable_panal();
	           	return self.gui.select_user({
	                'security':     true,
	                'current_user': self.pos.get_cashier(),
	                'title':      _t('Change Cashier'),
	                'cashier_window': true
	            }).then(function(user){
	                self.pos.set_cashier(user);
	                self.gui.chrome.widget.username.renderElement();
	            }).then(function () {
	            	self.gui.show_screen('payment');
	            });
            }
		},
		quick_delete_draft_order: function(event){
			var self = this;
        	var selectedOrder = this.pos.get_order();
        	var order_id = parseInt($(event.currentTarget).data('id'));
        	var selectedOrder = this.pos.get_order();
        	var result = self.pos.db.get_sale_note_by_id(order_id);
        	if (result && result.lines.length > 0) {
        		var params = {
    	    		model: 'pos.order',
    	    		method: 'unlink',
    	    		args: [result.id],
    	    	}
        		rpc.query(params, {async: false}).then(function(result){});
        	}
        	var sale_note_to_be_remove = self.pos.db.get_sale_note_by_id(result.id)
        	var sale_note_list = self.pos.db.get_sale_note_list();
        	sale_note_list = _.without(sale_note_list, _.findWhere(sale_note_list, { id: sale_note_to_be_remove.id }));
        	self.screens.sale_note_list.render_list(sale_note_list)
        	self.render_sale_note_order_list(sale_note_list);
        	self.pos.db.add_sale_note(sale_note_list)
		},
		sale_note_chrome: function(){
			var self = this;
			if($('#draggablePanelList').css('display') == 'none'){
				$('#draggablePanelList').animate({
    	            height: 'toggle'
    	            }, 200, function() {
    	        });
				self.render_sale_note_order_list(self.pos.db.get_sale_note_list());
				$('.head_data').html(_t("Orders"));
				$('.panel-body').html("Message-Box Empty");
			}else{
				$('#draggablePanelList').animate({
    	            height: 'toggle'
    	            }, 200, function() {
    	        });
			}
		},
		render_sale_note_order_list: function(orders){
        	var self = this;
        	if(orders){
        		var contents = $('.message-panel-body');
	            contents.html("");
	            var order_count_el = $('#draft_order_count');
	            contents.html("");
	            var temp = [];
	            var order_count = 0;
	            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
	                var order    = orders[i];
	                if(order.state == "draft"){
	                	order_count ++;
		                var orderlines = [];
		                order.amount_total = order.amount_total;
		            	var clientline_html = QWeb.render('SaleNoteQuickWidgetLine',{widget: this, order:order, orderlines:orderlines});
		                var clientline = document.createElement('tbody');
		                clientline.innerHTML = clientline_html;
		                clientline = clientline.childNodes[1];
		                contents.append(clientline);
	                }
	            }
	            self.pos.order_quick_draft_count = order_count
            	$('.notification-count').show();
            	$('.draft_order_count').text(order_count);
        	}
        },
		close_draggable_panal:function(){
			$('#draggablePanelList').animate({
	            height: 'toggle'
	            }, 200, function() {
	        });
		},
	});
});
