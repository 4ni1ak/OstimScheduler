# Apache License 2.0

# Copyright (c) 2025 Anıl Akpınar

# Bu yazılım, aşağıdaki koşullar altında kullanılabilir:

# 1. Kullanıcılar, yazılımı özgürce kullanabilir, değiştirebilir ve dağıtabilirler.
# 2. Dağıtım sırasında, yazılımın orijinal lisansı ve telif hakkı bildirimi belirtilmelidir.
# 3. Eğer yazılımda değişiklik yapılırsa, değişiklikler açıkça belirtildiği takdirde kullanılabilir.

# Bu yazılım, "olduğu gibi" sağlanmaktadır ve herhangi bir garanti verilmemektedir.

from dataclasses import dataclass
from typing import List, Dict, Optional
from itertools import combinations, product
import re

@dataclass
class TimeSlot:
    start_time: str
    end_time: str
    
    def __str__(self):
        return f"{self.start_time}-{self.end_time}"
    
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)

@dataclass
class Course:
    code: str
    name: str
    section: str
    classroom: str
    instructor: str
    time_slots: Dict[str, List[TimeSlot]]
    
    def add_time_slot(self, day: str, time_slot: TimeSlot):
        if day not in self.time_slots:
            self.time_slots[day] = []
        self.time_slots[day].append(time_slot)
        self.time_slots[day].sort(key=lambda x: x.start_time)
    def __hash__(self):
        return hash((self.code, self.section))
    
    def overlaps_with(self, other: 'Course') -> bool:
        for day, slots in self.time_slots.items():
            if day in other.time_slots:
                for slot1 in slots:
                    for slot2 in other.time_slots[day]:
                        if slot1.overlaps(slot2):
                            return True
        return False
    
    def __str__(self):
        return f"{self.code} {self.name} (Şube: {self.section})"

class Schedule:
    def __init__(self, courses: List[Course]):
        self.courses = courses
        self.days_order = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    
    def is_valid(self) -> bool:
        for c1, c2 in combinations(self.courses, 2):
            if c1.overlaps_with(c2):
                return False
        return True
    
    def get_daily_schedule(self) -> Dict[str, List[tuple[str, TimeSlot]]]:
        daily_schedule = {day: [] for day in self.days_order}
        
        for course in self.courses:
            for day, slots in course.time_slots.items():
                if day in daily_schedule:
                    for slot in slots:
                        daily_schedule[day].append((f"{course.code} (Şube: {course.section})", slot))
        
        for day in daily_schedule:
            daily_schedule[day].sort(key=lambda x: x[1].start_time)
        
        return daily_schedule
    
    def __str__(self):
        daily_schedule = self.get_daily_schedule()
        result = []
        
        for day in self.days_order:
            if day in daily_schedule and daily_schedule[day]:
                day_schedule = [f"{course} {slot}" for course, slot in daily_schedule[day]]
                result.append(f"{day}:\n  " + "\n  ".join(day_schedule))
        
        return "\n\n".join(result)

class CourseScheduler:
    def __init__(self):
        self.all_courses: Dict[str, List[Course]] = {}
    
    def add_course(self, course: Course):
        if course.code not in self.all_courses:
            self.all_courses[course.code] = []
        self.all_courses[course.code].append(course)
    # def list_all_courses(self) -> str:
    #     if not self.all_courses:
    #         return "Henüz eklenmiş ders bulunmamaktadır."

    #     result = []
    #     for course_code, courses in sorted(self.all_courses.items()):
    #         result.append(f"Ders Kodu: {course_code}")
    #         for course in courses:
    #             result.append(f"  Şube: {course.section}")
    #             result.append(f"  Ders Adı: {course.name}")
    #             result.append(f"  Sınıf: {course.classroom}")
    #             result.append(f"  Öğretim Elemanı: {course.instructor}")
    #             for day, slots in course.time_slots.items():
    #                 slot_str = ", ".join(str(slot) for slot in slots)
    #                 result.append(f"  {day}: {slot_str}")
    #             result.append("-" * 40) 

    #     return "\n".join(result)
    
    def parse_schedule(self, schedule_text: str):
        current_day = None
        for line in schedule_text.split('\n'):
            line = line.strip()
            if not line or line.startswith("Saat\t"):
                continue

            if not '\t' in line:
                current_day = line
                continue

            parts = line.split('\t')
            if len(parts) != 5:
                continue

            time_str, course_with_section, name, classroom, instructor = parts

            match = re.match(r"([A-Z]+ \d+)\((\d+)\)", course_with_section)
            if not match:
                continue

            code = match.group(1)
            section = match.group(2)

            start_time, end_time = time_str.split('-')
            time_slot = TimeSlot(start_time, end_time)

            if not instructor.strip():
                instructor = "Henüz Belirlenmemiş"

            course = None
            if code in self.all_courses:
                for existing_course in self.all_courses[code]:
                    if existing_course.section == section:
                        course = existing_course
                        break

            if course is None:
                course = Course(code, name, section, classroom, instructor, {})
                self.add_course(course)

            course.add_time_slot(current_day, time_slot)

    
    def get_numbered_course_list(self) -> List[str]:
        courses = sorted(self.all_courses.keys())
        return [f"{i+1}. {code}" for i, code in enumerate(courses)]
    
    def get_course_code_by_number(self, number: int) -> Optional[str]:
        courses = sorted(self.all_courses.keys())
        if 1 <= number <= len(courses):
            return courses[number - 1]
        return None
    
    def generate_possible_schedules(self, mandatory_courses: List[str]) -> List[Schedule]:
        possible_schedules = []
        section_combinations = []
        
        for course_code in mandatory_courses:
            if course_code in self.all_courses:
                section_combinations.append(self.all_courses[course_code])
        
        for combination in product(*section_combinations):
            schedule = Schedule(list(combination))
            if schedule.is_valid():
                possible_schedules.append(schedule)
        
        return possible_schedules
    
    def add_optional_courses(self, schedule: Schedule) -> Schedule:
        current_courses = set(schedule.courses)
        current_course_codes = {course.code for course in schedule.courses}
        selectable_courses = []

        for courses in self.all_courses.values():
            for course in courses:
                if course.code in current_course_codes:
                    continue
                selectable_courses.append(course)

        while True:
            if not selectable_courses:
                print("\nUygun seçmeli ders bulunamadı!")
                return Schedule(list(current_courses))

            print("\nAşağıdaki seçmeli dersler mevcut programa eklenebilir:")
            for i, course in enumerate(selectable_courses, 1):
                print(f"{i}. {course}")

            print("\nEklemek istediğiniz seçmeli derslerin numaralarını girin (virgülle ayırarak) veya geçmek için 'G' yazın:")
            selection = input("> ").strip().upper()

            if selection == 'G':
                return Schedule(list(current_courses)) 

            selected_numbers = [int(num.strip()) for num in selection.split(',') if num.strip().isdigit()]
            selected_courses = [selectable_courses[num - 1] for num in selected_numbers if 1 <= num <= len(selectable_courses)]

            valid_courses = []
            conflicted_courses = []
            for course in selected_courses:
                temp_schedule = Schedule(list(current_courses) + [course])
                if temp_schedule.is_valid():
                    valid_courses.append(course)
                else:
                    conflicted_courses.append(course)

            if conflicted_courses:
                print("\nSeçtiğiniz bazı dersler mevcut programınızla çakışıyor:")
                for course in conflicted_courses:
                    print(f"- {course}")

                print("\nTekrar seçmek ister misiniz? (E/H)")
                retry = input("> ").strip().upper()
                if retry == 'H':
                    return Schedule(list(current_courses))  
                else:
                    selectable_courses = [course for course in selectable_courses if course not in conflicted_courses]
            else:
                current_courses.update(valid_courses)
                return Schedule(list(current_courses))


def format_schedule(input_text):
    standard_header = "Saat	Ders Kodu	Ders Adı	Derslik	Öğretim Elemanı"
    input_text = input_text.replace("Tanımlı Ders Programı Bulunamadı!", standard_header)
    
    lines = input_text.strip().split('\n')
    
    formatted_output = []
    header = None
    current_day_classes = []
    
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    def process_day_data(day, header, classes):
        if not day:
            return []
        
        result = [day]
        
        if header:
            result.append(header)
        
        updated_classes = []
        for cls in classes:
            parts = cls.split('\t')
            if len(parts) < 5:
                parts.append("Henüz Girilmemiştir")
            updated_classes.append('\t'.join(parts))
        
        result.extend(updated_classes)
        result.append("")
        return result
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
            
        day_pair = line.split()
        found_days = []
        
        for word in day_pair:
            if word in days:
                found_days.append(word)
        
        if found_days:
            if current_day_classes:
                formatted_output.extend(process_day_data(found_days[0], header, current_day_classes))
                current_day_classes = []
            
            i += 1
            while i < len(lines) and "Saat" not in lines[i]:
                i += 1
            
            if i < len(lines):
                header = lines[i]
                i += 1
                
                first_day_classes = []
                while i < len(lines) and "Saat" not in lines[i]:
                    if lines[i].strip():
                        first_day_classes.append(lines[i].strip())
                    i += 1
                
                formatted_output.extend(process_day_data(found_days[0], header, first_day_classes))
                
                if i < len(lines) and "Saat" in lines[i]:
                    header = lines[i]
                    i += 1
                    
                    second_day_classes = []
                    while i < len(lines) and not any(day in lines[i] for day in days):
                        if lines[i].strip():
                            second_day_classes.append(lines[i].strip())
                        i += 1
                    if len(found_days) > 1:
                        formatted_output.extend(process_day_data(found_days[1], header, second_day_classes))
                continue
        i += 1
    if formatted_output and not formatted_output[-1]:
        formatted_output.pop()
    return '\n'.join(formatted_output)
def create_schedule(schedule_text: str):
    scheduler = CourseScheduler()
    scheduler.parse_schedule(schedule_text)
    # print(scheduler.list_all_courses())
    print("Mevcut dersler:")
    course_list = scheduler.get_numbered_course_list()
    for course in course_list:
        print(course)
    print("\nZorunlu dersleri seçin (virgülle ayırarak numara girin, örn: 1,3,5):")
    selection = input("> ").strip()
    selected_numbers = [int(num.strip()) for num in selection.split(',')]
    mandatory_codes = [scheduler.get_course_code_by_number(num) for num in selected_numbers]
    mandatory_codes = [code for code in mandatory_codes if code]
    possible_schedules = scheduler.generate_possible_schedules(mandatory_codes)
    
    if not possible_schedules:
        print("\nUygun program bulunamadı!")
        return
    
    print(f"\n{len(possible_schedules)} adet olası program bulundu:")
    for i, schedule in enumerate(possible_schedules, 1):
        print(f"\nProgram {i}:")
        print(schedule)
    
    print(f"\nHangi programı seçmek istersiniz? (1-{len(possible_schedules)}):")
    selection = int(input("> "))
    
    if 1 <= selection <= len(possible_schedules):
        selected_schedule = possible_schedules[selection - 1]
        
        print("\nSeçmeli dersleri eklemek ister misiniz? (E/H):")
        add_optional = input("> ").strip().upper() == 'E'
        
        final_schedule = scheduler.add_optional_courses(selected_schedule) if add_optional else selected_schedule
        
        print("\nNihai Ders Programınız:")
        print(final_schedule)
    else:
        print("Geçersiz seçim!")
def get_multiline_input():
    print("""
    Hoş geldiniz! Bu program, OBS profilinizdeki ders programınızı kullanarak derslerinizi kolayca seçmenize yardımcı olacaktır.

    1. **OBS Profilinize Girin:** OBS'yi açın ve genel işlemler bölümünde "Bölüm Ders Programı" sekmesini bulun.
    2. **Dönem Seçimi:** İlgili dönem için doğru seçeneği belirleyin.
    3. **Pazartesiden Sonra Tüm Günleri Seçin:** Pazartesi gününden başlayarak haftanın son gününe kadar tüm ders programınızı seçin.
    4. **Seçiminizi Kopyalayın:** Seçtiğiniz ders programını kopyalamak için **Ctrl + Shift + C** (veya sisteminizdeki uygun kopyalama kısayolu) tuşlarına basın.
    5. **Kopyalanan Veriyi Yapıştırın:** Kopyaladığınız ders programını aşağıdaki alana yapıştırmak için **Ctrl + Shift + V** tuşlarına basın.
    6. **Son Adım:** Programın doğru çalışabilmesi için **3 kez Enter** tuşuna basın.

    Bu adımları takip ettikten sonra program, kopyaladığınız ders programınızı işleyecek ve çıktıyı sağlayacaktır. 
    """)
    lines = []
    empty_line_count = 0
    
    while empty_line_count < 3:
        line = input()
        if line.strip() == "":
            empty_line_count += 1
        else:
            empty_line_count = 0
            lines.append(line)
            
    return "\n".join(lines)
if __name__ == "__main__":
    create_schedule(format_schedule(get_multiline_input()))
