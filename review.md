### app/lib/mongo.py:15
### [HIGH] Неполная проверка наличия индекса по 'district'
Проверка по имени индекса 'district_1' не учитывает случаи, когда индекс существует с другим именем или с одинаковой схемой но другим именем. Это может привести к дублированию индексов, что ухудшает производительность и использует дополнительное место. Лучше проверять наличие индекса по самому ключу.

**Почему важно:** Дублирование индексов замедляет операции записи и увеличивает память.

```diff
existing_indexes = collection.list_indexes()
index_key_exists = any(
    [idx['key']] == [('district', ASCENDING)] for idx in existing_indexes if 'key' in idx
)
if not index_key_exists:
    collection.create_index([('district', ASCENDING)], name='district_1')
```

### app/lib/mongo.py:15
### [MEDIUM] Получение списка индексов при каждом вызове
Вызов `collection.list_indexes()` происходит каждый раз при получении коллекции, что может быть неэффективно, особенно если коллекция крупная и вызовы частые.

**Почему важно:** Лишние сетевые запросы к MongoDB снижают производительность.

```diff
Рассмотреть кеширование проверки индекса или выполнение этого только при инициализации приложения, а не при каждом вызове.
```

### app/modules/routes.py:47
### [HIGH] Неэффективная вставка документов по одному
В цикле используется `collection.insert(entity.dict())` для каждого документа, что делает множество отдельных insert-операций вместо одной массовой вставки.

**Почему важно:** Это значительно медленнее для большого количества документов, увеличивает нагрузку на базу данных и может привести к таймаутам.

```diff
entities = [
    FlatDBEntity(
        **flat,
        psm=count_psm(flat),
        district=district,
        area=extract_area(flat),
    ).dict()
    for flat in data
    if district is not None
]
if entities:
    result = collection.insert_many(entities)
    response = result.inserted_ids
else:
    response = []
```

### app/lib/mongo.py:0
### [MEDIUM] Отсутствие тестов для изменений функций MongoDB
Изменения в логике получения коллекций, индексов, агрегации и запросов координат не покрыты тестами в данном diff. Необходимо добавить unit-тесты для проверки корректности создания индексов, агрегаций и фильтрации None-значений.

**Почему важно:** Без тестов высок риск регрессий, особенно при изменениях в бизнес-логике (например, фильтрация документов с _id=None).

# Code Review Summary

- **Улучшения читаемости:** Добавлены типизации, docstrings и переформатированные импорты, что повышает поддерживаемость.
- **Исправления логики:** Агрегация в `get_district_average_field_mapping` упрощена и корректно фильтрует None, проекция coords уточнена для избежания ошибок сериализации.
- **Потенциальные баги:** Неполная проверка индексов может привести к дубликатам; вставка по одному ухудшает производительность.
- **Производительность:** Операции с индексами и вставками выполняются неоптимально — лучше использовать массовые операции и кеширование.
- **Тестирование:** Отсутствуют тесты для ключевых изменений, что требует добавления unit-тестов.
- **Положительное:** Изменения делают код типизированным и более понятным без серьезных регрессий.

### app/modules/routes.py:0
### [HIGH] Incorrect tile name in Folium map
The tile name 'stamentoner' is likely a typo and should be 'Stamen Toner'. Folium's default tile providers use specific names; using an incorrect name may result in map rendering failures or errors. This is important to fix as it directly affects the heatmap functionality.

```diff
```diff
-    map_obj = folium.Map(
-        location=settings.COORDS[city_name],
-        tiles="stamentoner",
-        zoom_start=6,
-    )
+    map_obj = folium.Map(
+        location=settings.COORDS[city_name],
+        tiles="Stamen Toner",
+        zoom_start=6,
-    )
```
```

### app/modules/routes.py:0
### [MEDIUM] Unused import
The function `background_parsing` is imported but not used in the routes.py file. Removing unused imports improves code clarity and reduces potential confusion, as it avoids cluttering the namespace without benefit.

```diff
```diff
-from app.lib.lib import (
-    make_request,
-    get_district,
-    create_hist,
-    background_parsing,
-)
+from app.lib.lib import (
+    make_request,
+    get_district,
+    create_hist,
+)
```
```
# Code Review Summary

- Добавлены типизация, docstring'и и улучшена логика работы с индексами, что повышает надёжность кода.
- Исправлена aggregation pipeline в get_district_average_field_mapping для упрощения и предотвращения ошибок с None значениями.
- Улучшена читаемость кода за счёт переформатирования импортов, переименования переменных (например, _ на item).
- Основные проблемы: опечатка в названии tiles в heatmap, которая может сломать карту; неиспользуемый импорт background_parsing.
- Добавлен фильтр против None district в aggregation, что хорошо для обработки corner case.
- Нет новых тестов, но изменения в основном косметические и логические; рекомендуется добавить unit tests для новых функций.
