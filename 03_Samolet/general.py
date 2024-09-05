import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os


def load_data():
    """ Загрузка или создание таблицы """
    if os.path.exists('data.csv'):
        return pd.read_csv('data.csv')
    else:
        return pd.DataFrame(columns=["день недели", "дерево", "кол-во плодов"])


def save_data(df):
    """ Сохранение таблицы """
    df.to_csv('data.csv', index=False)


def is_natural_number(val):
    """ Проверка на натуральное число """
    try:
        return int(val) >= 0
    except:
        return False


# CSS стиль для смен фона
background_css = """
    <style>
    .main {
        background: url("https://i.ibb.co/Nn5fJmr/background.jpg");
        background-size: cover;
    }
    </style>
"""

default_css = """
    <style>
    .main {
        background: none;
    }
    </style>
"""


def display_graph(df):
    """ График количества плодов по деревьям и Линейный график количества фруктов по дням недели """
    # Создание агрегированных данных по "дерево" и "кол-во фруктов"
    chart_data = df.groupby(["день недели", "дерево"]).sum().reset_index()
    st.write("### График количества плодов по деревьям")
    st.bar_chart(chart_data.pivot(index="день недели", columns="дерево", values="кол-во плодов"))

    # Создание агрегированных данных по дням недели
    line_chart_data = df.groupby("день недели").sum().reset_index()
    st.write("### Линейный график количества фруктов по дням недели")
    st.line_chart(line_chart_data.set_index("день недели")["кол-во плодов"])


def display_linear_regression(df, days_of_week):
    """ Линейная регрессия (простое прогнозирование) """
    # Создание и обучение модели
    X = df[["день недели_num"]]
    y = df["кол-во плодов"]
    model = LinearRegression()
    model.fit(X, y)
    # Прогнозирование
    future_days_num = np.arange(len(days_of_week) + 7).reshape(-1, 1)
    predictions = model.predict(future_days_num)
    # Подготовка данных для отображения
    future_days = pd.DataFrame({
        "день недели_num": future_days_num.flatten(),
        "кол-во плодов": predictions
    })
    # Преобразование числовых кодов обратно в дни недели
    future_days["день недели"] = pd.Categorical.from_codes(
        future_days["день недели_num"] % len(days_of_week),  # Применяем модуль (%) чтобы коды не выходили за пределы существующих категорий
        categories=days_of_week,
        ordered=True
    )
    # Сортировка по дням недели
    future_days["день недели"] = pd.Categorical(future_days["день недели"], categories=days_of_week, ordered=True)
    future_days = future_days.sort_values("день недели")

    st.write("### Прогноз количества плодов на следующие дни недели")
    st.line_chart(future_days.set_index("день недели")["кол-во плодов"])

def display_correlation_analysis(df):
    """ Корреляционный анализ """
    # Вычисление корреляции
    correlation = df[["день недели_num", "кол-во плодов"]].corr().iloc[0, 1]
    st.write(f"### Корреляция между днем недели и количеством плодов: {correlation:.2f}")

    st.markdown("---")

    st.write(f"### Среднее кол-во плодов с деревьев в день за неделю:")
    average_fruits = df["кол-во плодов"].mean()
    expected_fruits = average_fruits + average_fruits * correlation
    col1, col2 = st.columns(2)
    col1.metric(label="Текущее", value=f'{average_fruits:.0f} плодов')
    col2.metric(label="Ожидаемое", value=f'{expected_fruits:.0f} плодов', delta=f'{correlation:.2f}')

    if correlation < 0:
        st.write(f"### Ух бл* казна пустеет")
        st.image('https://i.ibb.co/g9dkzTL/nostonk.jpg',
                 caption='*no stonk',
                 use_column_width=True)
    elif correlation > 0:
        st.write(f"### Бабка при бабках")
        st.image('https://i.ibb.co/jMFt7hv/stonk.jpg',
                 caption='*stonk',
                 use_column_width=True)

