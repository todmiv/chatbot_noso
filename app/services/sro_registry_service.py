# app/services/sro_registry_service.py
"""
Сервис для проверки членства в СРО НОСО через парсинг их сайта.
"""
import logging
import aiohttp
from bs4 import BeautifulSoup
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class SRORegistryService:
    """Сервис для работы с реестром СРО НОСО."""

    def __init__(self):
        self.base_url = "https://www.sronoso.ru/reestr/"
        self.timeout = aiohttp.ClientTimeout(total=15) # Увеличен таймаут

    async def check_membership_by_inn(self, inn: str) -> Optional[Dict]:
        """
        Проверяет статус членства организации в СРО НОСО по ИНН.
        
        Args:
            inn (str): ИНН организации (10 или 12 цифр).
            
        Returns:
            Optional[Dict]: Словарь с данными о членстве или None, если не найдено.
        """
        logger.info(f"[SRORegistryService] Checking membership for INN: {inn}")
        if not inn:
            logger.warning("[SRORegistryService] Empty INN provided.")
            return None

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Параметры для поиска по ИНН
                # Исправлена ошибка: ключ 'arrFilter_ff[INNNumber]' заменен на правильный 'arrFilter_pf[INNNumber]'
                # Также добавлено точное совпадение по ИНН с 'EXACT_MATCH_1=Y'
                params = {
                    "PAGEN_1": 1,
                    "arrFilter_pf[INNNumber]": inn,
                    "set_filter": "Y",
                    "EXACT_MATCH_1": "Y" # Для точного совпадения по ИНН
                }
                
                logger.debug(f"[SRORegistryService] Requesting URL: {self.base_url} with params: {params}")
                async with session.get(self.base_url, params=params) as response:
                    logger.debug(f"[SRORegistryService] Response status: {response.status}")
                    if response.status != 200:
                        logger.error(f"[SRORegistryService] HTTP error {response.status} for INN {inn}")
                        # Попробуем прочитать тело ответа для отладки
                        error_text = await response.text()
                        logger.debug(f"[SRORegistryService] Error response body: {error_text[:500]}...")
                        return None
                    
                    html = await response.text()
                    logger.debug(f"[SRORegistryService] Received HTML length: {len(html)}")
                    
            soup = BeautifulSoup(html, "html.parser")
            
            # Найдем таблицу результатов
            # Структура таблицы на сайте: 
            # Заголовки: №, Полное наименование legal entity, ИНН, Дата включения в реестр членов СРО, Статус
            table = soup.find('table', {'class': 'table table-bordered table-striped'})
            
            if not table:
                logger.warning("[SRORegistryService] Results table not found in HTML.")
                # Возможно, страница просто не содержит результатов, но структура таблицы отсутствует
                # Проверим, есть ли сообщение "ничего не найдено"
                if "ничего не найдено" in html.lower() or "не найдено" in html.lower():
                     logger.info("[SRORegistryService] Search returned 'not found' message.")
                else:
                     logger.warning("[SRORegistryService] Unexpected HTML structure, no table and no 'not found' message.")
                return None
                
            rows = table.find_all('tr')
            logger.debug(f"[SRORegistryService] Found {len(rows)} rows in table.")
            
            if len(rows) <= 1:  # Только заголовок или пустая таблица
                logger.info("[SRORegistryService] No results found in the table (only header or empty).")
                return None
                
            # Обычно первая строка - заголовок, начинаем со второй (rows[1:])
            for row in rows[1:]:
                cols = row.find_all('td')
                logger.debug(f"[SRORegistryService] Processing row with {len(cols)} columns.")
                # Ожидаем как минимум 5 колонок: №, Название, ИНН, Дата, Статус
                if len(cols) >= 5:
                    # Индексы могут отличаться, проверяем по содержимому или позиции
                    # Согласно структуре сайта:
                    # 0 - № (td)
                    # 1 - Полное наименование legal entity (td)
                    # 2 - ИНН (td)
                    # 3 - Дата включения (td)
                    # 4 - Статус (td)
                    org_inn = cols[2].text.strip()
                    status = cols[4].text.strip()
                    org_name = cols[1].text.strip()
                    join_date = cols[3].text.strip()
                    
                    logger.debug(f"[SRORegistryService] Row data - INN: '{org_inn}', Status: '{status}', Name: '{org_name}'")
                    
                    # Проверяем точное совпадение ИНН
                    if inn == org_inn:
                        is_member = status.lower() in ['член сро', 'член совета сро', 'претендент'] # Определяем, что считается "членом"
                        logger.info(f"[SRORegistryService] INN {inn} found. Status: '{status}', Is Member: {is_member}")
                        return {
                            "registry": "СРО НОСО",
                            "name": org_name,
                            "inn": org_inn,
                            "status": status,
                            "join_date": join_date,
                            "is_member": is_member,
                            "registry_url": str(response.url) if 'response' in locals() else self.base_url
                        }
                    else:
                        logger.debug(f"[SRORegistryService] INN mismatch in row: expected '{inn}', got '{org_inn}'")
                else:
                    logger.warning(f"[SRORegistryService] Row has less than 5 columns: {len(cols)}. Content: {[c.text.strip() for c in cols]}")
            
            logger.info(f"[SRORegistryService] INN {inn} not found in the results table.")
            return None
            
        except aiohttp.ClientError as e:
            logger.error(f"[SRORegistryService] Network error while checking INN {inn}: {e}")
            return None
        except Exception as e:
            logger.error(f"[SRORegistryService] Unexpected error while checking INN {inn}: {e}", exc_info=True)
            return None

# Глобальный экземпляр сервиса
sro_registry_service = SRORegistryService()
