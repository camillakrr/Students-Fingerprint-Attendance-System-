import random
import secrets
from datetime import datetime

import names
from pg4nosql.PostgresNoSQLClient import PostgresNoSQLClient


def create_students(db):
    students = db['students']
    fingerprints = []
    for i in range(0, 1000):
        first_name = names.get_first_name()
        last_name = names.get_last_name()
        year = random.randint(1, 4)
        group = random.randint(1, 10)
        fingerprint_hash = secrets.token_hex(nbytes=16)
        fingerprints.append(fingerprint_hash)
        students.put({'first_name': first_name, 'last_name': last_name, 'year': year, 'group': group,
                      'fingerprint_hash': fingerprint_hash},
                     auto_commit=False)
    students.commit()
    return fingerprints


def create_scanners(db):
    scanners = db['scanners']
    serial_numbers = []
    for i in range(100, 200):
        serial_number = random.randint(10000000000, 99999999999)
        serial_numbers.append(serial_number)
        scanners.put({'classroom': i, 'serial_number': serial_number}, auto_commit=False)
    scanners.commit()
    return serial_numbers


def create_classes(db):
    classes = db['classes']
    courses = ['Discrete Math and Logic', 'Data Structure and Algorithms', 'Analitical Geometry and Linear Algebra',
               'English', 'Introduction to Programming', 'Mathematical Analysis', 'Introduction to AI',
               'Data Modeling and Databases', 'Software Project', 'Probability and Statistics', 'Networks',
               'Control Theory', 'Digital Signal Processing', 'Information Retrieval', 'Data Mining',
               'Lean Software Development', 'Mechanics and Machines', 'Software System Design', 'Life Safety',
               'Practical Machine Learning and Deep Learning', 'Software Quality and Reliability']
    types = ['lecture', 'tutorial', 'lab']
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = ['9:00', '10:35', '12:10', '14:10', '15:45', '17:20', '18:55', '20:30']
    classrooms = dict()
    groups = dict()
    for i in range(1000):
        course = secrets.choice(courses)
        type = secrets.choice(types)
        classroom = random.randint(100, 200)
        year = random.randint(1, 4)
        group = random.randint(1, 10)
        weekday = secrets.choice(weekdays)
        time_slot = secrets.choice(time_slots).split(":")
        hours = time_slot[0]
        minutes = time_slot[1]
        if type == "lab":
            if weekday + hours + minutes + str(classroom) not in classrooms and weekday + hours + minutes + str(
                    year) + str(group) not in groups:
                classrooms[weekday + hours + minutes + str(classroom)] = "true"
                groups[weekday + hours + minutes + str(year) + str(group)] = "true"
                classes.put(
                    {"course": course, "type": type, "classroom": classroom, "year": year,
                     "groups": "{" + str(group) + "}",
                     "weekday": weekday, "start_time": {"hours": hours, "minutes": minutes}})
        else:
            if weekday + hours + minutes + str(classroom) not in classrooms:
                for j in range(10):
                    if weekday + hours + minutes + str(year) + str(j + 1) in groups:
                        break
                if j == 9:
                    classrooms[weekday + hours + minutes + str(classroom)] = "true"
                    for q in range(10):
                        groups[weekday + hours + minutes + str(year) + str(q + 1)] = "true"
                    classes.put(
                        {"course": course, "type": type, "classroom": classroom, "year": year,
                         "groups": "{1,2,3,4,5,6,7,8,9,10}",
                         "weekday": weekday, "start_time": {"hours": hours, "minutes": minutes}})


def create_attendance(db, fingerprints, serial_numbers):
    students = db['students']
    scanners = db['scanners']
    classes = db['classes']
    attendance = db['attendance']
    for i in range(100000):
        fingerprint_hash = secrets.choice(fingerprints)
        student = students.query("json->>'fingerprint_hash'='" + fingerprint_hash + "'")[0]
        student_id = student.id
        year = student.json['year']
        group = student.json['group']
        serial_number = secrets.choice(serial_numbers)
        scanner = scanners.query("json->>'serial_number'='" + str(serial_number) + "'")[0]
        classroom = scanner.json['classroom']
        unixtime = random.randint(1493078400, 1587772800)
        date = datetime.utcfromtimestamp(unixtime).strftime('%d.%m.%Y %H:%M')
        weekday = datetime.fromtimestamp(unixtime).strftime("%A")
        hours = int(datetime.fromtimestamp(unixtime).strftime("%H")) - 3
        minutes = int(datetime.fromtimestamp(unixtime).strftime("%M"))
        ts = hours * 60 + minutes
        timeslot = classes.query("json->>'classroom'='" + str(classroom) + "'AND json->>'year'='" + str(
            year) + "'AND array_position((json->>'groups')::integer[]," + str(
            group) + ") IS NOT NULL AND json->>'weekday'='" + weekday + "'AND ((json->>'start_time')::json->>'hours')::integer * 60 + ((json->>'start_time')::json->>'minutes')::integer<" + str(
            ts + 5) + "AND ((json->>'start_time')::json->>'hours')::integer * 60 + ((json->>'start_time')::json->>'minutes')::integer>" + str(
            ts - 90))
        if len(timeslot) == 1:
            class_id = timeslot[0].id
            start_time = timeslot[0].json['start_time']
            time = int(start_time['hours']) * 60 + int(start_time['minutes'])
            if ts <= time:
                status = "in time"
            else:
                status = "late"
            attendance.put(
                {"student_id": student_id, "class_id": class_id, "date": date, "status": status})


'''
select all late ppl
'''


def query1(db):
    table = db['attendance']
    file = open("file1", "w")
    output = table.query("json->>'status'='late'")
    file.write(str(len(output)))
    file.write(" late people in total.\n")
    for row in output:
        file.write(str(row))
        file.write("\n")
    file.close()


'''
select ppl who are not late
'''


def query2(db):
    table = db['attendance']
    file = open("file2", "w")
    output = table.query("json->>'status'='in time'")
    file.write(str(len(output)))
    file.write(" people came on time.\n")
    for row in output:
        file.write(str(row))
        file.write("\n")
    file.close()


'''
select only ppl who are late by more than 10 minutes
'''


def query3(db):
    file = open("file3", "w")
    str1 = "select id as id, json->>'student_id' as student, json->>'class_id' as class, json->>'date' as date, json->>'status' as status from attendance where json->>'status' = 'late'"
    str2 = "select id as id, json->>'course' as course, json->>'type' as type, json->'start_time'->>'hours' as hours, json->'start_time'->>'minutes' as minutes from classes"
    str3 = "abs(extract(hour from cast(a.date as date)) * 60 + extract(minute from cast(a.date as date)) - cast(c.hours as int) * 60 + cast(c.minutes as int)) > 10"
    query = "select * from ({}) a inner join ({}) c on cast(a.class as int) = c.id and({})".format(str1, str2, str3)
    output = db.execute(query)
    file.write(str(len(output)))
    file.write(" people late by more than 10 minutes.\n")
    for row in output:
        file.write(str(row))
        file.write("\n")
    file.close()


'''
show popularity of each type of class for each course
'''


def query4(db):
    file = open("file4", "w")
    str1 = "select id as id, json->>'student_id' as student, json->>'class_id' as class from attendance"
    str2 = "select id as id, json->>'course' as course, json->>'type' as type from classes"
    query0 = "select * from ({}) a inner join ({}) c on cast(a.class as int) = c.id".format(str1, str2)
    query = "select course, type, count(*) as amount from ({}) as joined group by course, type order by course, amount desc".format(query0)
    output = db.execute(query)
    file.write("Popularity of classes:\n")
    for row in output:
        file.write(str(row))
        file.write("\n")
    file.close()


'''
average amount of people present
'''


def query5(db):
    file = open("file5", "w")
    str1 = "select id as id, json->>'student_id' as student, json->>'class_id' as class from attendance"
    str2 = "select id as id, json->>'course' as course, json->>'type' as type from classes"
    query0 = "select * from ({}) a inner join ({}) c on cast(a.class as int) = c.id".format(str1, str2)
    query = "select round(avg(amount), 0) from (select course, type, count(*) as amount from ({}) as joined group by course, type) as amount".format(query0)
    output = db.execute(query)
    file.write("Average amount of people among all classes:\n")
    for row in output:
        file.write(str(row))
        file.write("\n")
    file.close()


def main():
    client = PostgresNoSQLClient(host='localhost', port='5432', user='postgre', password='postgre')
    db = client['attendance_system']
    #fingerprints = create_students(db)
    #serial_numbers = create_scanners(db)
    #create_classes(db)
    #create_attendance(db, fingerprints, serial_numbers)
    query1(db)
    query2(db)
    query3(db)
    query4(db)
    query5(db)


if __name__ == '__main__':
    main()