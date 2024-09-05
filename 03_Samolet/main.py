import streamlit as st
import pandas as pd
from general import *

# Инициализация таблицы
df = load_data()

# Определение CSS стиля для фона
# Создайте тумблер
use_custom_background = st.checkbox("Использовать кастомный фон для темной темы (16:9 и не подгоняется :С )", value=False)
# Примените CSS стиль в зависимости от состояния тумблера
if use_custom_background:
    st.markdown(background_css, unsafe_allow_html=True)
else:
    st.markdown(default_css, unsafe_allow_html=True)

# Заголовок приложения
st.title("Контроль плодов с деревьев Агафьи Алексеевны")
st.write("Здравствуйте Агафья Алексеевна! Как у вас дела?")

# Поля для добавления новой записи
st.markdown("---")
st.write("### Давайте запишем новые данные:")
day_of_week = st.selectbox("День недели", ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"], key="add_day_of_week")
tree_name = st.text_input("Название вашего дерева", key="add_tree_name")
fruits_count = st.text_input("Кол-во плодов с него", value="1", key="add_fruits_count")

# Добавление новой записи
if st.button("Зафиксировать эти новости", key="add_button"):
    # Валидация полей
    if len(tree_name) > 50:
        st.error("Название дерева не может превышать 50 символов! Извинитесь.")
    elif any(character.isdigit() for character in tree_name):
        st.error("В деревьях не могут быть цифры, извинитесь.")
    elif not is_natural_number(fruits_count):
        st.error("Количество плодов должно быть натуральным числом или нулём! Извинитесь.")
    else:
        # Добавление новой строки в DataFrame (данные передаются как список)
        new_row = pd.DataFrame({
            "день недели": [day_of_week],
            "дерево": [tree_name],
            "кол-во плодов": [int(fruits_count)]
        })
        # Используем pd.concat для добавления новой строки к существующему DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        st.success("Мы всё запомнили!")

st.markdown("---")
# Отображение таблицы через st.data_editor
if not df.empty:
    st.write("### Наши сокровища")

    # Настройка поля "день недели" как селектбокс
    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    # Преобразование дня недели в категориальный тип с правильным порядком
    df["день недели"] = pd.Categorical(df["день недели"], categories=days_of_week, ordered=True)
    df["день недели_num"] = df["день недели"].cat.codes

    df = df.sort_values("день недели")
    df["Удалить"] = False
    # Отображаем и редактируем таблицу с конфигурацией колонок
    edited_df = st.data_editor(
        df,
        column_config={
            "день недели": st.column_config.SelectboxColumn(
                "День недели",  # Заголовок
                options=days_of_week  # Опции для выбора
            ),
            "дерево": st.column_config.TextColumn(
                "Дерево",  # Заголовок
                max_chars=50  # Максимальное количество символов
            ),
            "кол-во фруктов": st.column_config.NumberColumn(
                "Кол-во плодов",  # Заголовок
                min_value=1  # Ограничение на минимальное значение
            ),
            "Удалить": st.column_config.CheckboxColumn("Выделение")  # Добавляем столбец с чекбоксами для удаления
        },
        num_rows="fixed",
        # num_rows="dynamic",
        key="data_editor",
        use_container_width=True
    )
    # Кнопка для удаления выбранных записей
    if st.button("Забыть выделенную информацию"):
        # Фильтруем строки, где чекбокс "Удалить" установлен в True
        df = edited_df[edited_df["Удалить"] == False].drop(columns=["Удалить"])
        save_data(df)
        st.success("Мы больше такого не помним!")
        st.rerun()  # Перезагружаем интерфейс после удаления

    # Сохраняем изменения, если таблица редактировалась
    if edited_df is not None:
        df = edited_df
        save_data(df)
        # st.success("Таблица успешно обновлена!")

    st.markdown("---")

    # ГРАФИКИ
    display_graph(df)

    st.markdown("---")

    # АНАЛИТИЧЕСКИЕ ГРАФИКИ
    display_linear_regression(df, days_of_week)
    display_correlation_analysis(df)

else:
    st.write("Таблица пуста.")
