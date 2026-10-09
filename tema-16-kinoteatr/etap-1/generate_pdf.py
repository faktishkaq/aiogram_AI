#!/usr/bin/env python3
"""PDF Этап 1 (пункты 1–3), более «человечный» текст."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

BLUE = colors.Color(0 / 255, 112 / 255, 192 / 255)


def main():
    out = Path("/workspace/tema-16-kinoteatr/etap-1/tema16-etap1-punkty1-3.pdf")
    out2 = Path("/workspace/tema-16-kinoteatr/etap-1/TZ_Etap1_Upravlenie_kinoteatrom.pdf")
    art = Path("/opt/cursor/artifacts")
    art.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleRU",
            fontName="DejaVuBold",
            fontSize=13,
            leading=17,
            alignment=TA_CENTER,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubRU",
            fontName="DejaVu",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1RU",
            fontName="DejaVuBold",
            fontSize=12,
            leading=15,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2RU",
            fontName="DejaVuBold",
            fontSize=10.5,
            leading=13,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyRU",
            fontName="DejaVu",
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BoldRU",
            fontName="DejaVuBold",
            fontSize=10,
            leading=13,
            spaceBefore=4,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletRU",
            fontName="DejaVu",
            fontSize=10,
            leading=13,
            leftIndent=10,
            spaceAfter=2,
        )
    )
    styles.add(ParagraphStyle(name="CellRU", fontName="DejaVu", fontSize=7.5, leading=9.5))
    styles.add(ParagraphStyle(name="CellBoldRU", fontName="DejaVuBold", fontSize=7.5, leading=9.5))
    styles.add(
        ParagraphStyle(
            name="NoteRU",
            fontName="DejaVu",
            fontSize=9,
            leading=12,
            textColor=colors.grey,
            spaceBefore=10,
        )
    )

    def P(text, style="BodyRU"):
        return Paragraph(text, styles[style])

    def cell(text, bold=False):
        return Paragraph(str(text), styles["CellBoldRU" if bold else "CellRU"])

    def make_table(headers, rows, widths):
        data = [[cell(h, True) for h in headers]]
        for row in rows:
            data.append([cell(c) for c in row])
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.86, 0.92, 0.96)),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return t

    story = []
    story.append(P("Тема 16. Управление кинотеатром", "TitleRU"))
    story.append(P("Этап 1. Сбор и анализ требований", "TitleRU"))
    story.append(P("Пункты 1–3", "TitleRU"))
    story.append(
        P(
            "Изучение предметной области, роли пользователей, бизнес-правила "
            "(по методичке Stage_1_theory).",
            "SubRU",
        )
    )

    # 1
    story.append(P("1. Изучение предметной области", "H1RU"))
    story.append(
        P(
            "Кинотеатр показывает фильмы в нескольких залах. На каждый сеанс продают билеты "
            "на конкретные места. Цена зависит от того, какое место (обычное или VIP) и на какой "
            "сеанс идёт человек. Зритель в приложении смотрит афишу, схему зала и свободные места. "
            "Администрация смотрит, насколько зал заполнен и сколько денег принесли сеансы."
        )
    )

    story.append(P("Кто участвует", "H2RU"))
    story.append(P("•  Зритель — выбирает сеанс, покупает билет, иногда возвращает его.", "BulletRU"))
    story.append(P("•  Кассир — продаёт и возвращает билеты на кассе, помогает найти свободные места.", "BulletRU"))
    story.append(P("•  Администратор — заводит фильмы и сеансы, настраивает залы, смотрит отчёты.", "BulletRU"))

    story.append(P("Основные процессы", "H2RU"))

    story.append(P("Планирование сеанса.", "BoldRU"))
    story.append(
        P(
            "Администратор берёт фильм из проката, выбирает зал и время, ставит базовую цену. "
            "Перед сохранением нужно убедиться, что в этом зале на это время уже ничего не стоит. "
            "В данных появляется новый сеанс со статусом «запланирован»."
        )
    )

    story.append(P("Продажа билета.", "BoldRU"))
    story.append(
        P(
            "Зритель (в приложении) или кассир (на кассе) выбирает сеанс, смотрит схему зала, "
            "отмечает свободные места и оплачивает. Цена считается как базовая цена сеанса, "
            "умноженная на коэффициент типа места. В данных появляются билеты со статусом «продан», "
            "а выбранные места на этот сеанс считаются занятыми."
        )
    )

    story.append(P("Возврат билета.", "BoldRU"))
    story.append(
        P(
            "Зритель или кассир находит билет и оформляет возврат, если ещё можно. "
            "Статус билета меняется на «возвращён», место снова становится свободным."
        )
    )

    story.append(P("Просмотр афиши и мест.", "BoldRU"))
    story.append(
        P(
            "Зритель или кассир выбирает дату (и при желании фильм), смотрит список сеансов "
            "и открывает схему зала. Данные только читаются, ничего не меняется."
        )
    )

    story.append(P("Отчёт по заполняемости и выручке.", "BoldRU"))
    story.append(
        P(
            "Администратор выбирает период или конкретный сеанс и смотрит, сколько мест занято "
            "и какая сумма продаж. Снова только чтение и подсчёты."
        )
    )

    story.append(P("Ограничения", "H2RU"))
    story.append(
        make_table(
            ["Тип", "Что нельзя нарушать", "Как обычно закрывают"],
            [
                ["Структурные", "У сеанса всегда есть фильм и зал", "NOT NULL, внешний ключ"],
                ["Структурные", "У места всегда есть зал и тип", "NOT NULL, внешний ключ"],
                [
                    "Бизнес-правила",
                    "Одно место на один сеанс нельзя продать дважды",
                    "уникальность / проверка в приложении",
                ],
                [
                    "Бизнес-правила",
                    "В одном зале сеансы не должны накладываться по времени",
                    "триггер или проверка в приложении",
                ],
                [
                    "Бизнес-правила",
                    "Место в билете должно быть из зала этого сеанса",
                    "триггер или проверка в приложении",
                ],
                ["Бизнес-правила", "Цена не бывает отрицательной", "CHECK"],
                ["Технические", "В одном зале нет двух мест с одним рядом и номером", "UNIQUE"],
                ["Технические", "Логин сотрудника уникален", "UNIQUE"],
            ],
            [3.0 * cm, 8.3 * cm, 5.2 * cm],
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        P(
            "Откуда берутся правила: из самой логики работы кассы (нельзя вернуть то, что не продавали), "
            "из реальности (одно кресло — один человек на сеанс) и из политики кинотеатра "
            "(VIP дороже обычного места)."
        )
    )

    # 2
    story.append(P("2. Роли пользователей", "H1RU"))
    story.append(
        P(
            "Роль — это не конкретный человек, а набор того, что такому пользователю можно делать "
            "в системе."
        )
    )

    story.append(P("Администратор", "H2RU"))
    story.append(
        make_table(
            ["Что делает", "Что нужно на входе", "Что получается", "Чего нельзя"],
            [
                [
                    "Добавляет или правит фильм",
                    "название, длительность, рейтинг, жанр",
                    "фильм появляется / обновляется",
                    "длительность > 0",
                ],
                [
                    "Настраивает зал и места",
                    "название зала, ряды и номера, типы мест",
                    "появляются зал и места",
                    "нельзя два одинаковых «ряд + номер»",
                ],
                [
                    "Создаёт сеанс",
                    "фильм, зал, время, цена",
                    "появляется сеанс",
                    "зал не занят; конец позже начала; цена ≥ 0",
                ],
                [
                    "Отменяет сеанс",
                    "какой сеанс",
                    "статус «отменён»",
                    "нужно решить, что с уже проданными билетами",
                ],
                ["Смотрит отчёты", "период, зал или фильм", "выручка и заполняемость", "—"],
                [
                    "Ведёт сотрудников",
                    "ФИО, логин, роль",
                    "сотрудник появляется в системе",
                    "логин не должен повторяться",
                ],
            ],
            [3.8 * cm, 4.8 * cm, 3.8 * cm, 4.1 * cm],
        )
    )

    story.append(P("Кассир", "H2RU"))
    story.append(
        make_table(
            ["Что делает", "Что нужно на входе", "Что получается", "Чего нельзя"],
            [
                ["Ищет сеанс", "дата, фильм или зал", "список сеансов", "—"],
                ["Смотрит свободные места", "выбранный сеанс", "схема зала с занятостью", "—"],
                [
                    "Продаёт билет",
                    "сеанс, места, данные зрителя",
                    "билет «продан»",
                    "место занято; сеанс отменён",
                ],
                [
                    "Возвращает билет",
                    "номер / id билета",
                    "статус «возвращён»",
                    "билет не был продан или срок вышел",
                ],
                ["Выдаёт билет зрителю", "билет", "зритель получает билет", "билет должен быть действующим"],
            ],
            [3.6 * cm, 4.6 * cm, 4.0 * cm, 4.3 * cm],
        )
    )

    story.append(P("Зритель", "H2RU"))
    story.append(
        make_table(
            ["Что делает", "Что нужно на входе", "Что получается", "Чего нельзя"],
            [
                ["Смотрит афишу", "дата, можно фильтр по фильму", "список сеансов", "—"],
                ["Выбирает места", "сеанс", "видит свободные места", "нельзя брать уже занятые"],
                ["Покупает билет", "сеанс, места, телефон или email", "билеты оформлены", "место заняли раньше"],
                ["Смотрит свои билеты", "аккаунт / контакты", "список своих покупок", "чужие билеты не видит"],
                [
                    "Отменяет покупку",
                    "свой билет",
                    "статус «возвращён»",
                    "только свои и только пока разрешён срок",
                ],
            ],
            [3.6 * cm, 4.6 * cm, 4.0 * cm, 4.3 * cm],
        )
    )

    # 3
    story.append(P("3. Бизнес-правила", "H1RU"))
    story.append(
        P(
            "Бизнес-правило — то, что в данных всегда должно быть правдой. "
            "Пишем в формате: «… должно / не должно …». Для учебного проекта достаточно 5–7 правил. "
            "Ниже семь — они закрывают продажу билетов, расписание сеансов и схему зала."
        )
    )
    for t in [
        "1. На один сеанс одно и то же место не должно быть продано больше одного раза "
        "(если билет ещё «продан» или «забронирован»).",
        "2. Базовая цена сеанса и цена билета должны быть больше либо равны нулю.",
        "3. Время окончания сеанса должно быть позже времени начала.",
        "4. Место в билете должно относиться к залу того сеанса, на который билет оформлен.",
        "5. В одном зале сеансы не должны пересекаться по времени.",
        "6. В одном зале пара «ряд + номер места» должна быть уникальной.",
        "7. У билета статус должен быть только из набора: «продан», «забронирован», «возвращён». "
        "Билет со статусом «возвращён» не должен занимать место.",
    ]:
        story.append(P(t, "BulletRU"))

    story.append(Spacer(1, 4))
    story.append(
        P(
            "Как это потом ляжет в БД: цены и даты — через CHECK, уникальность места в зале — через UNIQUE, "
            "«одно место на сеанс» — через уникальность или проверку в приложении, пересечение сеансов "
            "и «место из нужного зала» — скорее через триггер или логику приложения."
        )
    )

    story.append(P("Какие правила к каким процессам относятся", "H2RU"))
    story.append(
        make_table(
            ["Процесс", "Какие правила держат"],
            [
                ["Планирование сеанса", "2, 3, 5"],
                ["Продажа билета", "1, 2, 4, 7"],
                ["Возврат билета", "7"],
                ["Афиша и отчёты", "1 и 7 — иначе свободные места и выручка посчитаются криво"],
            ],
            [6.5 * cm, 10 * cm],
        )
    )

    story.append(
        P(
            "Дальше по методичке идут состав данных, объёмы, частота операций и производительность — "
            "в эту часть работы их не включал.",
            "NoteRU",
        )
    )

    def page_no(canvas, doc_):
        canvas.saveState()
        canvas.setFont("DejaVu", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2, 12 * mm, f"Страница {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=page_no, onLaterPages=page_no)
    data = out.read_bytes()
    out2.write_bytes(data)
    (art / "tema16-etap1-punkty1-3.pdf").write_bytes(data)
    (art / "TZ_Etap1_Upravlenie_kinoteatrom.pdf").write_bytes(data)
    print("OK", out, len(data))


if __name__ == "__main__":
    main()
