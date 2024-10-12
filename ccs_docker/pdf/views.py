import io

from django.http import HttpResponse

from ccs_docker.backend.models import Crime
from ccs_docker.backend.models import Criminal


# Create your views here.
def crime_pdf(request, uuid):
    import re

    # import reportlab
    non_alpha_numeric = re.compile(r"[^0-9a-zA-Z]+")
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.platypus import Spacer
    from reportlab.platypus import Table

    print("11111")
    styles = getSampleStyleSheet()
    crime = Crime.nodes.get(uuid=uuid)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    flowables = []
    paragraph_1 = Paragraph(str(crime), styles["Heading3"])

    data = [
        [
            Paragraph(str(criminal), styles["Normal"]),
            Paragraph(str(involvement), styles["Normal"]),
        ]
        for criminal, involvement in crime.criminal_list
    ]
    data.insert(
        0,
        [
            Paragraph("Criminal", styles["Heading4"]),
            Paragraph("Status", styles["Heading4"]),
        ],
    )
    paragraph_3 = Table(
        data,
        style=[("GRID", (0, 0), (-1, -1), 1, (0, 0, 0))],
        repeatRows=1,
        colWidths=(400, 100),
    )
    flowables.append(paragraph_1)
    if crime.gist:
        paragraph_2 = Paragraph(crime.gist, styles["BodyText"])
        flowables.append(paragraph_2)
    flowables.append(Spacer(0, 10))
    flowables.append(paragraph_3)
    doc.build(flowables)
    pdf_value = buffer.getvalue()
    buffer.close()
    file_name = re.sub(non_alpha_numeric, "_", str(crime))
    print(file_name)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={file_name}.pdf"

    response.write(pdf_value)
    return response


def criminal_pdf(request, uuid):
    from reportlab.lib import utils
    from reportlab.lib.units import cm

    def get_image(path, width=1 * cm):
        img = utils.ImageReader(path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        return Image(path, width=width, height=(width * aspect))

    import re

    # import reportlab
    non_alpha_numeric = re.compile(r"[^0-9a-zA-Z]+")
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Image
    from reportlab.platypus import Paragraph
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.platypus import Spacer
    from reportlab.platypus import Table

    styles = getSampleStyleSheet()
    criminal = Criminal.nodes.get(uuid=uuid)
    crimerecord = criminal.crimerecord
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    flowables = []
    paragraph_1 = Paragraph(str(criminal), styles["Heading3"])
    paragraph_1_1 = Paragraph("Crime-record:", styles["Heading4"])
    crime_record = [
        [
            Paragraph(crime, styles["Normal"]),
            Paragraph(str(status), styles["Normal"]),
            Paragraph(coaccused, styles["Normal"]),
        ]
        for _, crime, status, coaccused in crimerecord[0]
    ]
    crime_record.insert(
        0,
        [
            Paragraph("Case", styles["Heading4"]),
            Paragraph("Status", styles["Heading4"]),
            Paragraph("Co- accused", styles["Heading4"]),
        ],
    )
    paragraph_2 = Table(
        crime_record,
        style=[("GRID", (0, 0), (-1, -1), 1, (0, 0, 0))],
        repeatRows=1,
        colWidths=(300, 100, 50),
    )
    flowables.append(paragraph_1)
    flowables.append(paragraph_1_1)
    flowables.append(paragraph_2)
    flowables.append(Spacer(0, 10))
    paragraph_2_1 = Paragraph("Co-accused list:", styles["Heading4"])
    co_accused = [
        [Paragraph(str(sl_no), styles["Normal"]), Paragraph(criminal, styles["Normal"])]
        for _, criminal, sl_no in crimerecord[1]
    ]
    co_accused.insert(
        0,
        [
            Paragraph("Sl No.", styles["Heading4"]),
            Paragraph("Person", styles["Heading4"]),
        ],
    )
    paragraph_3 = Table(
        co_accused,
        style=[("GRID", (0, 0), (-1, -1), 1, (0, 0, 0))],
        repeatRows=1,
        colWidths=(50, 400),
    )
    flowables.append(paragraph_2_1)
    flowables.append(paragraph_3)
    paragraph_3_1 = Paragraph("Photos:", styles["Heading4"])
    flowables.append(paragraph_3_1)
    for image in criminal.album:
        try:
            flowables.append(get_image(image, width=8 * cm))
        except Exception as e:
            print(str(e))
    doc.build(flowables)
    pdf_value = buffer.getvalue()
    buffer.close()
    file_name = re.sub(non_alpha_numeric, "_", str(criminal))
    print(file_name)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={file_name}.pdf"

    response.write(pdf_value)
    return response
