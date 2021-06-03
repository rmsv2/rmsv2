from rmsv2 import settings
from rms.models import Customer, Reservation, Instance, Device, AbstractItem
from django.conf import settings
from django.utils import formats, timezone
from django.contrib.auth.models import User
from django.utils.timezone import datetime

from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from io import BytesIO
import os.path
import textwrap
from typing import Iterable, List

pdfmetrics.registerFont(TTFont('Arial', os.path.join(settings.BASE_DIR, 'static/arial.ttf')))
pdfmetrics.registerFont(TTFont('Arial Bold', os.path.join(settings.BASE_DIR, 'static/arial_bold.ttf')))


class PDF:

    def __init__(self):
        if settings.PDF_BACKGROUND is not None:
            self.base_pdf = PdfFileReader(open(settings.PDF_BACKGROUND, 'rb'))
        else:
            self.base_pdf = None
        self.output_pdf = PdfFileWriter()
        self._pdf_buffer = BytesIO()
        self.pdf = canvas.Canvas(self._pdf_buffer, pagesize=A4)
        self.top_border = A4[1]-settings.PDF_SAVE_TOP*mm
        self.bottom_border = settings.PDF_SAVE_BOTTOM*mm+5*mm
        self.page_number = 1

        self.pdf.setFont('Arial', 7)
        self.pdf.drawString(170 * mm, self.bottom_border, 'Seite {}'.format(self.page_number))

    def _new_page(self):
        self.pdf.showPage()
        self.page_number += 1
        self.top_border = A4[1]-settings.PDF_SAVE_TOP*mm

        self.pdf.setFont('Arial', 7)
        self.pdf.drawString(170 * mm, self.bottom_border, 'Seite {}'.format(self.page_number))

    def draw_address(self, customer: Customer):
        self.pdf.setFont('Arial', 12)
        self.pdf.setFontSize(8)
        self.pdf.drawString(25*mm, 246.5*mm, settings.PDF_FROM_LINE)
        self.pdf.setFontSize(11)
        self.pdf.drawString(25*mm, 233*mm, str(customer))
        if customer.mailing_address.mailbox is not None:
            self.pdf.drawString(25*mm, 228*mm, 'Postfach: {}'.format(customer.mailing_address.mailbox))
        else:
            self.pdf.drawString(25*mm, 228*mm, '{} {}'.format(customer.mailing_address.street,
                                                              customer.mailing_address.number))
        self.pdf.drawString(25*mm, 223*mm, '{} {}'.format(customer.mailing_address.zip_code,
                                                          customer.mailing_address.city))

        if self.top_border > 200*mm:
            self.top_border = 200*mm

    def draw_type(self, type: str, extension: int=0):
        self.pdf.setFont('Arial Bold', 18)
        self.pdf.drawCentredString(156*mm, 250*mm, '- {} -'.format(type))
        if extension > 0:
            self.pdf.setFont('Arial', 10)
            self.pdf.drawCentredString(156*mm, 246*mm, 'Ergänzung #{}'.format(extension))
        if self.top_border > 246*mm:
            self.top_border = 246*mm

    def draw_reservation_header(self, reservation: Reservation,
                                creation_date: datetime=timezone.localtime(timezone.now())):
        name = textwrap.wrap(reservation.name, width=22)

        top_pos = 240
        self.pdf.setFont('Arial Bold', 11)
        self.pdf.drawRightString(145*mm, top_pos*mm, 'Projekt:')
        self.pdf.drawRightString(145*mm, (top_pos-len(name)*5)*mm, 'Ausgabe:')
        self.pdf.drawRightString(145*mm, (top_pos-5-len(name)*5)*mm, 'Rückgabe:')
        self.pdf.drawRightString(145*mm, (top_pos-10-len(name)*5)*mm, 'ID:')

        self.pdf.setFont('Arial', 11)
        index = 0
        for line in name:
            self.pdf.drawString(147*mm, (top_pos-index*5)*mm, line)
            index += 1
        self.pdf.drawString(147*mm, (top_pos-len(name)*5)*mm, formats.date_format(creation_date, 'DATETIME_FORMAT'))
        self.pdf.drawString(147*mm, (top_pos-5-len(name)*5)*mm, formats.date_format(reservation.end_date,
                                                                                    'DATETIME_FORMAT'))
        self.pdf.drawString(147*mm, (top_pos-10-len(name)*5)*mm, reservation.full_id)

        if self.top_border > (top_pos-10-len(name)*5)*mm:
            self.top_border = (top_pos-10-len(name)*5)*mm

    def draw_signing_fields(self, customer: Customer, user: User):

        if self.top_border-self.bottom_border < 25.5*mm:
            self._new_page()

        p = self.pdf.beginPath()
        p.moveTo(25*mm, self.top_border-20*mm)
        p.lineTo(90*mm, self.top_border-20*mm)
        p.moveTo(115*mm, self.top_border-20*mm)
        p.lineTo(185*mm, self.top_border-20*mm)
        self.pdf.drawPath(p)
        self.pdf.setFont('Arial', 7)
        self.pdf.drawCentredString(57.5*mm, self.top_border-23*mm, str(customer))
        self.pdf.drawCentredString(57.5*mm, self.top_border-25.5*mm, '(Entleiher)')

        self.pdf.drawCentredString(147.5*mm, self.top_border-23*mm, '{} {}'.format(user.first_name, user.last_name))
        self.pdf.drawCentredString(147.5*mm, self.top_border-25.5*mm, '(Verleiher)')

        self.top_border = self.top_border-25.5*mm

    def draw_rent_item_table(self, instances: Iterable[Instance], abstract_items: Iterable[AbstractItem]):
        # grouping instances by devices
        devices = dict()
        for instance in instances:
            if instance.device not in devices:
                devices[instance.device] = []
            devices[instance.device].append(instance)

        # grouping abstract items by name
        grouped_abstract_items = {}
        for item in abstract_items:
            if item.name not in grouped_abstract_items:
                grouped_abstract_items[item.name] = 0
            grouped_abstract_items[item.name] += item.amount

        def draw_device(device: Device, instances: List[Instance]):
            if self.top_border-self.bottom_border < 11*mm:
                self._new_page()
                draw_table_header()
            page_break = False
            self.pdf.setFont('Arial', 10)
            self.pdf.drawString(26*mm, self.top_border-4.2*mm, device.name)
            self.pdf.drawRightString(184*mm, self.top_border-4.2*mm, str(len(instances)))
            self.pdf.setFontSize(7)
            self.pdf.drawString(30*mm, self.top_border-7*mm, 'Hersteller: {}'.format(device.vendor))
            self.pdf.drawString(30*mm, self.top_border-9.8*mm, 'Modell: {}'.format(device.model_number))
            device_bottom = self.top_border-9.8*mm

            for instance in instances:
                if self.top_border - self.bottom_border < 9*mm:
                    p = self.pdf.beginPath()
                    p.moveTo(25*mm, self.top_border-2*mm)
                    p.lineTo(185*mm, self.top_border-2*mm)
                    self.pdf.drawPath(p)
                    self._new_page()
                    draw_table_header()
                self.pdf.setFont('Arial', 7)
                self.pdf.drawString(90*mm, self.top_border-4*mm, 'Seriennummer: {}'.format(instance.serial_number))
                self.top_border -= 4*mm

            if self.top_border > device_bottom and not page_break:
                self.top_border = device_bottom

            p = self.pdf.beginPath()
            p.moveTo(25*mm, self.top_border-2*mm)
            p.lineTo(185*mm, self.top_border-2*mm)
            self.pdf.drawPath(p)

            self.top_border -= 2*mm

        def draw_abstract_item(name: str, amount: int):
            name_wrapped = textwrap.wrap(name, width=60)

            if self.top_border - self.bottom_border < len(name_wrapped)*4.2*mm:
                self._new_page()
                draw_table_header()

            self.pdf.setFont('Arial', 10)
            for idx, line in enumerate(name_wrapped):
                self.pdf.drawString(26*mm, self.top_border-((idx+1)*4.2)*mm, line)
            self.pdf.drawRightString(184*mm, self.top_border-4.2*mm, str(amount))

            self.top_border -= (len(name_wrapped)*4.2*mm+2*mm)

            p = self.pdf.beginPath()
            p.moveTo(25 * mm, self.top_border)
            p.lineTo(185 * mm, self.top_border)
            self.pdf.drawPath(p)

        def draw_table_header():
            p = self.pdf.beginPath()
            p.moveTo(25*mm, self.top_border-10*mm)
            p.lineTo(185*mm, self.top_border-10*mm)
            self.pdf.drawPath(p)
            self.pdf.setFont('Arial Bold', 10)
            self.pdf.drawString(25*mm, self.top_border-9.5*mm, 'Info')
            self.pdf.drawRightString(185*mm, self.top_border-9.5*mm, 'Anzahl')
            self.top_border = self.top_border-10*mm

        draw_table_header()
        for device, instances in devices.items():
            draw_device(device, instances)

        for name, amount in grouped_abstract_items.items():
            draw_abstract_item(name, amount)

    def get_pdf(self) -> bytes:
        self.pdf.save()
        content_pdf = PdfFileReader(self._pdf_buffer)
        final_buffer = BytesIO()
        final_pdf = PdfFileWriter()
        for i in range(0, content_pdf.getNumPages()):
            page = content_pdf.getPage(i)
            if self.base_pdf is not None:
                page.mergePage(self.base_pdf.getPage(0))
            final_pdf.addPage(page)
        final_pdf.write(final_buffer)
        return final_buffer.getvalue()

    def save_pdf(self, path: str):
        with open(path, 'wb') as outfile:
            outfile.write(self.get_pdf())
            outfile.close()
