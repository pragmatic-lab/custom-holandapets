import xlsxwriter

class ReportFormats(object):
    
    def __init__(self, workbook):
        if not isinstance(workbook, xlsxwriter.Workbook):
            raise TypeError("Se espera un tipo xlsxwriter.Workbook")
        self._FORMATS_DEFINITIONS = {
            'bold' : {'bold': True, 'text_wrap': True},
            'integer' : {'num_format': '0'},
            'integer_bold' : {'num_format': '0', 'bold': True},
            'number' : {'num_format': '#,##0.00'},
            'money' : {'num_format': '$#,##0.00'},
            'money_enter' : {'num_format': '$#,##0'},
            'number_bold' : {'num_format': '#,##0.00', 'bold': True},
            'money_bold' : {'num_format': '$#,##0.00', 'bold': True},
            'money_enter_bold' : {'num_format': '$#,##0'},
            'date': {'num_format': 'dd/mm/yyyy'},
            'datetime': {'num_format': 'dd/mm/yyyy h:m:s'},
            'date_bold': {'num_format': 'dd/mm/yyyy', 'bold': True},
            'datetime_bold': {'num_format': 'dd/mm/yyyy h:m:s', 'bold': True},
            'merge_center': {'align': 'center', 'valign': 'vcenter', 'bold': True},
            'percent' : {'num_format': '0.00%'},
            'percent_bold' : {'num_format': '0.00%', 'bold': True},
        }
        self._FORMATS = {
            'bold' : workbook.add_format(self._FORMATS_DEFINITIONS.get('bold', {})), 
            'integer' : workbook.add_format(self._FORMATS_DEFINITIONS.get('integer', {})),
            'integer_bold' : workbook.add_format(self._FORMATS_DEFINITIONS.get('integer_bold', {})),
            'number' : workbook.add_format(self._FORMATS_DEFINITIONS.get('number', {})), 
            'money' : workbook.add_format(self._FORMATS_DEFINITIONS.get('money', {})),
            'money_enter' : workbook.add_format(self._FORMATS_DEFINITIONS.get('money_enter', {})), 
            'number_bold' : workbook.add_format(self._FORMATS_DEFINITIONS.get('number_bold', {})), 
            'money_bold' : workbook.add_format(self._FORMATS_DEFINITIONS.get('money_bold', {})), 
            'money_enter_bold' : workbook.add_format(self._FORMATS_DEFINITIONS.get('money_enter_bold', {})),
            'date': workbook.add_format(self._FORMATS_DEFINITIONS.get('date', {})),
            'datetime': workbook.add_format(self._FORMATS_DEFINITIONS.get('datetime', {})),
            'date_bold': workbook.add_format(self._FORMATS_DEFINITIONS.get('date_bold', {})),
            'datetime_bold': workbook.add_format(self._FORMATS_DEFINITIONS.get('datetime_bold', {})),
            'merge_center': workbook.add_format(self._FORMATS_DEFINITIONS.get('merge_center', {})),
            'percent': workbook.add_format(self._FORMATS_DEFINITIONS.get('percent', {})),
            'percent_bold': workbook.add_format(self._FORMATS_DEFINITIONS.get('percent_bold', {})),
        }
        
    def GetFormat(self, format_name):
        return self._FORMATS.get(format_name, '')
    
    def GetFormatDefinition(self, format_name):
        return self._FORMATS_DEFINITIONS.get(format_name, {})
    
    def GetNewFormatFromTemplate(self, workbook, format_name):
        return workbook.add_format(self._FORMATS_DEFINITIONS.get(format_name, {}))
