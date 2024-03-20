import csv
import glob
import io
import json

import pandas as pd
import yaml
from tqdm import tqdm


def read_lines(file_name):
    """Read a utf-8 file line by line to a list"""
    words = []
    with io.open(file_name, mode="r", encoding="utf-8") as f:
        for line in f.readlines():
            words.append(line.strip())
    return words


def write_lines(file_name, lines):
    """Read a utf-8 file line by line to a list"""
    with io.open(file_name, mode="w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.strip() + '\n')


def read_json_file(file_path):
    with open(file_path, mode='r', encoding='utf8') as f:
        json_data = json.load(f)
        return json_data


def write_json_file(path, content):
    with io.open(path, 'w', encoding='utf8') as fw:
        json.dump(content, fw, ensure_ascii=False, indent=2)


def read_tsv_file(file_path):
    data_list = []
    with open(file_path, 'r', encoding='utf8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        for row in reader:
            data_list.append(row)
    data_list.remove(data_list[0])
    return data_list


def write_tsv_file(file_path, header, content):
    with io.open(file_path, 'w', encoding='utf8') as fw:
        tsv_writer = csv.writer(fw, delimiter='\t')
        tsv_writer.writerow(header)
        for item in content:
            tsv_writer.writerow(item.values())


def read_json(file):
    with open(file, 'r', encoding='utf-8') as fin:
        d = json.load(fin)
    return d


def save_json(data, file):
    with open(file, 'w', encoding='utf-8') as out:
        json.dump(data, out, ensure_ascii=False, indent=4)


def folder2df(folder, out):
    df = pd.DataFrame()
    files = glob.glob(folder + '/*/*.tsv', recursive=True)
    for file_name_in in tqdm(files):
        try:
            f = pd.read_csv(file_name_in, sep='\t', header=None,
                            quoting=csv.QUOTE_NONE, encoding='utf-8').dropna().iloc[:, :2]
        except:
            print('Error load file %s' % file_name_in)
        df = df.append(f, ignore_index=True)
    df.to_csv(out, index=False, sep='\t')
    return df


def read_yaml(file):
    with open(file) as fp:
        content = yaml.load(fp, Loader=yaml.FullLoader)
    return content


def iterate_lines(folder_name, ext='txt'):
    """
    Read all lines from all text file adn return filename, index and line
    """
    files = glob.glob(folder_name + '/**/*.' + ext, recursive=True)
    for file_name_in in files:
        with open(file_name_in, mode='r', encoding='utf-8') as f:
            idx = 0
            for line in f.readlines():
                idx += 1
                yield file_name_in, idx, line.strip()
