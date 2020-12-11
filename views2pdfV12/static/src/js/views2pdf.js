// Odoo 12
odoo.define('views2pdf.views2pdf', function (require) {
    "use strict";
    var core = require('web.core');

    var WebClient = require('web.WebClient');
    var session = require('web.session');

    var ListController = require('web.ListController');
    var FormController = require('web.FormController');
    var PivotController = require('web.PivotController');
    var GraphController = require('web.GraphController');
    var CalendarController = require('web.CalendarController');
    var KanbanController = require('web.KanbanController');

    var _t = core._t;
    var QWeb = core.qweb;



    // UPDATE 'web.ListController'
    ListController.include({
        // OVERRIDE 'web.ListController.renderButtons()'
        renderButtons: function ($node) {
            // APPLY SUPER
            this._super.apply(this, arguments);
            var self = this;
            // UPDATE HEADER BUTTONS
            if (this.$buttons) {
                // ADD EVENT LISTENER TO NEW 'PRINT' HEADER BUTTON
                this.$buttons.find('#create_pdf').on('click', function (event) {
                    event.preventDefault();
                    self.generatePDF();
                });
            }
        },
        // ADD NEW FUNCTION 'generatePDF()' TO 'web.ListController'
        generatePDF: function() {
            var form = $('.o_view_controller');
            var cache_width = form.width();
            var a4 = [800, 841.89];  // A4 PAPER SIZE
            // CREATE CANVAS OBJECT
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            // CREATE PDF OBJECT
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var img = canvas.toDataURL("image/png");
                    var doc = new jsPDF({
                        unit: 'px',
                        format: 'letter',
                        orientation: 'landscape'
                    });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('list.pdf');
                    form.width(cache_width);
                });
            }
            $('body').scrollTop(0);
            createPDF();
        },
    });



    // UPDATE 'web.FormController'
    FormController.include({
        // OVERRIDE 'web.FormController.renderButtons()'
        renderButtons: function($node) {
            // APPLY SUPER
            this._super.apply(this, arguments);
            var self = this;
            // UPDATE HEADER BUTTONS
            if (this.$buttons) {
                // ADD EVENT LISTENER TO NEW 'PRINT' HEADER BUTTON
                this.$buttons.on('click', '#create_pdf', function (event) {
                    event.preventDefault();
                    self.generatePDF();
                });
            }
        },
        // ADD NEW FUNCTION 'generatePDF()' TO 'web.FormController'
        generatePDF: function() {
            var form = $('.o_view_controller');
            var cache_width = form.width();
            var a4 = [800, 841.89];  // A4 PAPER SIZE
            // CREATE CANVAS OBJECT
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            // CREATE PDF OBJECT
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var img = canvas.toDataURL("image/png");
                    var doc = new jsPDF({
                        unit: 'px',
                        format: 'letter',
                        orientation: 'landscape'
                    });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('form.pdf');
                    form.width(cache_width);
                });
            }
            $('body').scrollTop(0);
            createPDF();
        },
    });



    // UPDATE 'web.PivotController'
    PivotController.include({
        // OVERRIDE 'web.PivotController.renderButtons()'
        renderButtons: function($node) {
            // APPLY SUPER
            this._super.apply(this, arguments);
            var self = this;
            // UPDATE HEADER BUTTONS
            if (this.$buttons) {
                // ADD EVENT LISTENER TO NEW 'PRINT' HEADER BUTTON
                this.$buttons.on('click', '#create_pdf', function (event) {
                    event.preventDefault();
                    self.generatePDF();
                });
            }
        },
        // ADD NEW FUNCTION 'generatePDF()' TO 'web.PivotController'
        generatePDF: function() {
            var form = $('.o_view_controller');
            var cache_width = form.width();
            var a4 = [800, 841.89];  // A4 PAPER SIZE
            // CREATE CANVAS OBJECT
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            // CREATE PDF OBJECT
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var img = canvas.toDataURL("image/png");
                    var doc = new jsPDF({
                        unit: 'px',
                        format: 'letter',
                        orientation: 'landscape'
                    });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('pivot.pdf');
                    form.width(cache_width);
                });
            }
            $('body').scrollTop(0);
            createPDF();
        },
    });



    // UPDATE 'web.GraphController'
    GraphController.include({
        // OVERRIDE 'web.GraphController.renderButtons()'
        renderButtons: function($node) {
            // APPLY SUPER
            this._super.apply(this, arguments);
            var self = this;
            // UPDATE HEADER BUTTONS
            if (this.$buttons) {
                // ADD EVENT LISTENER TO NEW 'PRINT' HEADER BUTTON
                this.$buttons.on('click', '#create_pdf', function (e) {
                    e.preventDefault();
                    self.generatePDF();
                });
            }
        },
        // ADD NEW FUNCTION 'generatePDF()' TO 'web.GraphController'
        generatePDF: function() {
            // CREATE PDF OBJECT
            function createPDF() {
                var svg = $('.o_view_controller').find('svg')[0];
                svgAsPngUri(svg, {}, function(uri) {
                    var doc = new jsPDF({
                        unit: 'px',
                        format: 'letter',
                        orientation: 'landscape'
                    });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(uri, 'PNG', 0, 60, 500,300);
                    doc.save('graph.pdf');
                });
            }
            $('body').scrollTop(0);
            createPDF();
        },
    });



    // UPDATE 'web.CalendarController'
    CalendarController.include({
        // OVERRIDE 'web.CalendarController.renderButtons()'
        renderButtons: function($node) {
            // APPLY SUPER
            this._super.apply(this, arguments);
            var self = this;
            // UPDATE HEADER BUTTONS
            if (this.$buttons) {
                // ADD EVENT LISTENER TO NEW 'PRINT' HEADER BUTTON
                this.$buttons.on('click', '#create_pdf', function (event) {
                    event.preventDefault();
                    self.generatePDF();
                });
            }
        },
        // ADD NEW FUNCTION 'generatePDF()' TO 'web.CalendarController'
        generatePDF: function() {
            var form = $('.o_view_controller');
            var cache_width = form.width();
            var a4 = [800, 841.89];  // A4 PAPER SIZE
            // CREATE CANVAS OBJECT
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            // CREATE PDF OBJECT
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var img = canvas.toDataURL("image/png");
                    var doc = new jsPDF({
                        unit: 'px',
                        format: 'letter',
                        orientation: 'landscape'
                    });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('calendar.pdf');
                    form.width(cache_width);
                });
            }
            $('body').scrollTop(0);
            createPDF();
        },
    });



    // UPDATE 'web.KanbanController'
    KanbanController.include({
        // OVERRIDE 'web.KanbanController.renderButtons()'
        renderButtons: function($node) {
            // APPLY SUPER
            this._super.apply(this, arguments);
            var self = this;
            // UPDATE HEADER BUTTONS
            if (this.$buttons) {
                // ADD EVENT LISTENER TO NEW 'PRINT' HEADER BUTTON
                this.$buttons.on('click', '#create_pdf', function (event) {
                    event.preventDefault();
                    self.generatePDF();
                });
            }
        },
        // ADD NEW FUNCTION 'generatePDF()' TO 'web.KanbanController'
        generatePDF: function() {
            var form = $('.o_view_controller');
            var cache_width = form.width();
            var a4 = [800, 841.89];  // A4 PAPER SIZE
            // CREATE CANVAS OBJECT
            function getCanvas() {
                form.width((a4[0] * 1.33333) - 80).css('max-width', 'none');
                return html2canvas(form, {
                    imageTimeout: 2000,
                    removeContainer: true
                });
            }
            // CREATE PDF OBJECT
            function createPDF() {
                getCanvas().then(function (canvas) {
                    var img = canvas.toDataURL("image/png");
                    var doc = new jsPDF({
                        unit: 'px',
                        format: 'letter',
                        orientation: 'landscape'
                    });
                    var title = $('ol.breadcrumb').find('li.active').html();
                    doc.setFont("helvetica");
                    doc.setFontType("bold");
                    doc.setTextColor(0,0,255);
                    doc.text(title, 20, 30);
                    doc.addImage(img, 'JPEG', 20, 60);
                    doc.save('kanban.pdf');
                    form.width(cache_width);
                });
            }
            $('body').scrollTop(0);
            createPDF();
        },
    });
});
