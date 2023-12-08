from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('SimHei', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SimHei.ttf')))

def header(canvas, doc):
    '''set a logo on the left and two lines of text on the right.'''
    # 设置字体
    canvas.setFont('SimHei', 12)  # 使用 SimHei 字体
    text1 = "广州呈源生物免疫技术有限公司"
    text2 = "400-995-0930|www.rootpath.com"
    # 计算文本宽度
    text_width = canvas.stringWidth(text1, 'SimHei', 12)
    text_width2 = canvas.stringWidth(text2, 'Helvetica-Bold', 12)

    # 计算绘制位置
    page_width = doc.pagesize[0]
    margin = 0.5*inch

    # 添加文本
    text_y_position = doc.height + 0.75*inch
    canvas.drawString(page_width - text_width - 0.6*inch, text_y_position, text1)
    canvas.drawString(page_width - text_width2 - margin, text_y_position - 0.25*inch, text2)

    # 添加图像作为页眉
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("base:", base)
    logo_height = 27.5
    logo_y_position = text_y_position -20  # 使 logo 与第一行文本的顶部对齐
    canvas.drawImage(os.path.join(base, 'static',"rootpath.logo.png"), 0.6*inch, logo_y_position, width=120, height=logo_height)


def render_to_pdf(data, header_func=header):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.75*inch, bottomMargin=0.5*inch)  # 留出足够的页眉空间

    styles = getSampleStyleSheet()
    Story = []

    # 标题
    Story.append(Paragraph(data.get('vector_name', ''), styles['Title']))
    Story.append(Spacer(1, 12))

    # iU20
    Story.append(Paragraph(f"iU20: {data.get('iu20', '')}", styles['Normal']))
    Story.append(Spacer(1, 12))

    # iD20
    Story.append(Paragraph(f"iD20: {data.get('id20', '')}", styles['Normal']))
    Story.append(Spacer(1, 12))

    # vector_map，长文本自动换行
    NC3 = data.get('NC3', '')
    NC5 = data.get('NC5', '')
    vector_seq = data.get('vector_map', '')
    vector_combined_seq = NC3 + vector_seq + NC5
    vector_map_paragraph = Paragraph(vector_combined_seq, styles['Normal'])
    Story.append(vector_map_paragraph)

    doc.build(Story, onFirstPage=header_func, onLaterPages=header_func)
    
    buffer.seek(0)
    return buffer