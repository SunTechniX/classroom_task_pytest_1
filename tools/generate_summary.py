# tools/generate_summary.py
import subprocess
import sys
import re
import os

def run_command(cmd, shell=False):
    result = subprocess.run(
        cmd, shell=shell, capture_output=True, text=True, cwd=os.getcwd()
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def parse_pytest_results(stdout):
    pattern = r"^(tests/[^:]+::\w+)\s+(PASSED|FAILED|ERROR|SKIPPED)$"
    matches = re.findall(pattern, stdout, re.MULTILINE)
    return {test_id: (status == "PASSED") for test_id, status in matches}

def main():
    # === Шаг 1: Запуск pytest и парсинг результатов ===
    print("🔍 Запуск тестов...")
    pytest_out, pytest_err, _ = run_command([sys.executable, "-m", "pytest", "-v", "--tb=short"])
    
    with open("pytest_output.log", "w", encoding="utf-8") as f:
        f.write(pytest_out + "\n" + pytest_err)

    results = parse_pytest_results(pytest_out)

    # === Шаг 2: Проверка маркеров через check_markers.py ===
    print("🔍 Проверка маркеров...")
    _, markers_err, markers_code = run_command([sys.executable, "tools/check_markers.py"])
    markers_ok = (markers_code == 0)

    # === Шаг 3: Оценка заданий ===
    task1_tests = [
        "tests/test_calculator.py::test_add",
        "tests/test_calculator.py::test_subtract",
        "tests/test_calculator.py::test_multiply",
        "tests/test_calculator.py::test_fail_intentionally",
    ]
    task2_tests = [
        "tests/test_string_utils.py::test_uppercase",
        "tests/test_string_utils.py::test_reverse",
    ]

    def evaluate_task(test_list, expect_fail_on_last=False):
        score = 0
        total = len(test_list) * 10
        details = []
        for i, test_id in enumerate(test_list):
            if test_id not in results:
                details.append(f"❌ Тест не найден")
                continue
            passed = results[test_id]
            if expect_fail_on_last and i == len(test_list) - 1:
                # Последний тест должен упасть
                if not passed:
                    score += 10
                    details.append("✅ Упал (ожидаемо)")
                else:
                    details.append("⚠️ Не упал (должен был!)")
            else:
                if passed:
                    score += 10
                    details.append("✅")
                else:
                    details.append("❌")
        return score, total, details

    task1_score, task1_max, task1_details = evaluate_task(task1_tests, expect_fail_on_last=True)
    task2_score, task2_max, task2_details = evaluate_task(task2_tests, expect_fail_on_last=False)

    total_score = task1_score + task2_score
    total_max = task1_max + task2_max
    percentage = round(total_score / total_max * 100) if total_max > 0 else 0

    # === Шаг 4: Формирование Summary ===
    summary = []

    summary.append("## 📊 ИТОГОВЫЙ ОТЧЕТ ПО ВСЕМ ЗАДАНИЯМ")
    summary.append("")
    summary.append("### 📈 Сводная таблица")
    summary.append("| Задание | Баллы | Максимум | Статус |")
    summary.append("|---------|-------|----------|--------|")

    def status_emoji(score, max_score):
        if score == max_score:
            return "✅"
        elif score > 0:
            return "⚠️"
        else:
            return "❌"

    summary.append(f"| Задание 1: Калькулятор и тесты | {task1_score} | {task1_max} | {status_emoji(task1_score, task1_max)} |")
    summary.append(f"| Задание 2: Строковые функции и тесты | {task2_score} | {task2_max} | {status_emoji(task2_score, task2_max)} |")
    summary.append(f"| **ВСЕГО** | **{total_score}** | **{total_max}** | **{percentage}%** |")
    summary.append("")

    # Детали по тестам (опционально — можно убрать для краткости)
    summary.append("### 🔍 Детали по тестам")
    summary.append("**Задание 1:**")
    for test, detail in zip(task1_tests, task1_details):
        name = test.split("::")[1]
        summary.append(f"- `{name}` → {detail}")
    summary.append("")
    summary.append("**Задание 2:**")
    for test, detail in zip(task2_tests, task2_details):
        name = test.split("::")[1]
        summary.append(f"- `{name}` → {detail}")
    summary.append("")

    # Результат проверки маркеров
    summary.append("### 🏷️ Проверка маркеров (@pytest.mark)")
    if markers_ok:
        summary.append("✅ Найдены маркеры: `@pytest.mark.math`, `@pytest.mark.string`")
    else:
        summary.append("❌ Маркеры не обнаружены или указаны неверно")
    summary.append("")

    # Найденные файлы
    summary.append("### 📁 Найденные файлы:")
    for fname in ["tests/test_calculator.py", "tests/test_string_utils.py", "README.md"]:
        if os.path.exists(fname):
            summary.append(f"✅ `{fname}` — найден")
        else:
            summary.append(f"❌ `{fname}` — отсутствует")
    summary.append("")

    # Итоговая оценка
    summary.append(f"### 🏆 Итоговая оценка: **{total_score} / {total_max}**")
    if total_score == total_max and markers_ok:
        summary.append("\n🎉 **ПОЗДРАВЛЯЕМ! Все задачи выполнены корректно!**")
    else:
        summary.append("\n💡 **Рекомендация**: проверьте наличие маркеров и поведение фейлящегося теста.")

    summary_text = "\n".join(summary)

    # Вывод в консоль
    print(summary_text)

    # Запись в GitHub Actions Summary (если запущено в CI)
    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        with open(github_summary, "a", encoding="utf-8") as f:
            f.write(summary_text)
    else:
        # Локально — сохраняем для просмотра
        with open("SUMMARY.md", "w", encoding="utf-8") as f:
            f.write(summary_text)

if __name__ == "__main__":
    main()