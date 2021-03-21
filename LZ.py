from bitarray import bitarray
import sys
import argparse


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--decoder', default='LZ77')
    parser.add_argument('-a', '--action', default='enc')
    parser.add_argument('-of', '--openfile', default='123.txt')
    parser.add_argument('-wf', '--writefile', default='123.txt')

    return parser

class LZ77:

    def __init__(self):
        print("выбран LZ77")
        self.lookahead_buffer_size = 15  # length of match is at most 4 bits

    def compress(self, input_file_path, output_file_path):
        data = None
        i = 0
        output_buffer = bitarray(endian='big')

        try: # пытаемся прочитать файл
            with open(input_file_path, 'rb') as input_file:
                data = input_file.read()
        except IOError: # Ловим ошибку чтения
            print('Не удалось открыть файл, возможно он уже используется.')
            raise

        while i < len(data): # Пока не дойдём до последнего символа файла

            match = self.findLongestMatch(data, i) # ищём самое длинное совпадение

            if match: # если нашли, отмечаем 1 бит совпадения и добавляем смещение
                (bestMatchDistance, bestMatchLength) = match

                output_buffer.append(True)
                output_buffer.frombytes(bytes([bestMatchDistance >> 4]))
                output_buffer.frombytes(bytes([((bestMatchDistance & 0xf) << 4) | bestMatchLength]))
                i += bestMatchLength

            else: # если не нашли, то добавляем в словарь ложь и записываем 8 битный символ
                output_buffer.append(False)
                output_buffer.frombytes(bytes([data[i]]))
                i += 1

        output_buffer.fill() # Дополняем буфер нулями, если число бит не кратно 8

        try: # Пытаемся записать полученные результаты в файл
            with open(output_file_path, 'wb') as output_file:
                output_file.write(output_buffer.tobytes())
                print("Сжатие прошло успешно, сохранено в {}".format(output_file_path))
                return None
        except IOError:
            print('Не удалось открыть файл, возможно он уже используется.')
            raise

    def decompress(self, input_file_path, output_file_path):
        data = bitarray(endian='big')
        output_buffer = []

        try: # пытаемся прочитать файл
            with open(input_file_path, 'rb') as input_file:
                data.fromfile(input_file)
        except IOError:
            print('Не удалось открыть файл, возможно он уже используется.')
            raise

        while len(data) >= 9: # пока длина данных для обработки больше или равна 9 (1 бит для метки и 8 для символа)
            flag = data.pop(0) # читаем и сразу удаляем метку

            if not flag: # Если 0 то возвращаем значение след. 8 эл-тов и удаляем их из обработчика
                byte = data[0:8].tobytes()
                output_buffer.append(byte)
                del data[0:8]
            else: # если 1 то возвращаем 2 бита информации, находим длину закодированного блока и вносим в выходной файл каждый бит
                byte1 = ord(data[0:8].tobytes())
                byte2 = ord(data[8:16].tobytes())

                del data[0:16]
                distance = (byte1 << 4) | (byte2 >> 4)
                length = (byte2 & 0xf)

                for i in range(length):
                    output_buffer.append(output_buffer[-distance])
        out_data = b''.join(output_buffer)

        try: # пытаемся открыть файл для записи
            with open(output_file_path, 'wb') as output_file:
                output_file.write(out_data)
                print("Распаковка прошла успешно, сохранено в {}".format(output_file_path))
                return None
        except IOError:
            print('Не удалось открыть файл, возможно он уже используется.')
            raise

    def findLongestMatch(self, data, current_position): # функция поиска наилучшей подстроки в буфере
        end_of_buffer = min(current_position + self.lookahead_buffer_size, len(data) + 1) # определение конца буфера

        best_match_distance = -1 #
        best_match_length = -1 # устанавливаем отрицательные значения чтобы не перекодировать совпадения из 1 символа

        for j in range(current_position + 2, end_of_buffer):
            start_index = max(0, current_position - 20)
            substring = data[current_position:j]
            for i in range(start_index, current_position):
                repetitions = len(substring) // (current_position - i)
                last = len(substring) % (current_position - i)
                matched_string = data[i:current_position] * repetitions + data[i:i + last]
                if matched_string == substring and len(substring) > best_match_length:
                    best_match_distance = current_position - i
                    best_match_length = len(substring)
        if best_match_distance > 0 and best_match_length > 0:
            return (best_match_distance, best_match_length)
        return None


class LZ78:
    def __init__(self):
        print("выбран LZ78")

    def compress(self, input_file_path, output_file_path):
        input_file = open(input_file_path, 'r')
        encoded_file = open(output_file_path, 'w')
        data = input_file.read()
        dict_of_codes = {data[0]: '1'}
        encoded_file.write('0' + data[0])
        data = data[1:]
        comb = ''
        code = 2
        for char in data:
            comb += char
            if comb not in dict_of_codes:
                dict_of_codes[comb] = str(code)
                if len(comb) == 1:
                    encoded_file.write('0' + comb)
                else:
                    encoded_file.write(dict_of_codes[comb[0:-1]] + comb[-1])
                code += 1
                comb = ''

    def decompress(self, input_file_path, output_file_path):
        encoded_file = open(input_file_path, 'r')
        decoded_file = open(output_file_path, 'w')
        data = encoded_file.read()
        dict_of_codes = {'0': '', '1': data[1]}
        decoded_file.write(dict_of_codes['1'])
        data = data[2:]
        comb = ''
        code = 2
        for char in data:
            if char in '1234567890':
                comb += char
            else:
                dict_of_codes[str(code)] = dict_of_codes[comb] + char
                decoded_file.write(dict_of_codes[comb] + char)
                comb = ''
                code += 1


parser = createParser()
namespace = parser.parse_args(sys.argv[1:])
if namespace.decoder == "LZ77":
    coder = LZ77()
    if namespace.action == "enc":
        LZ77.compress(coder, namespace.openfile, namespace.writefile)
    elif namespace.action == "dec":
        LZ77.decompress(coder, namespace.openfile, namespace.writefile)
elif namespace.decoder == "LZ78":
    coder = LZ78()
    if namespace.action == "enc":
        LZ78.compress(coder, namespace.openfile, namespace.writefile)
    elif namespace.action == "dec":
        LZ78.decompress(coder, namespace.openfile, namespace.writefile)