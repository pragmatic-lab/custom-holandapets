# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from odoo.http import request
from odoo.addons.bus.controllers.main import BusController


class SaleNoteController(BusController):

    def _poll(self, dbname, channels, last, options):
        """Add the relevant channels to the BusController polling."""
        if options.get('sale.note'):
            channels = list(channels)
            lock_channel = (
                request.db,
                'sale.note',
                options.get('sale.note')
            )
            channels.append(lock_channel)
        return super(SaleNoteController, self)._poll(dbname, channels, last, options)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
