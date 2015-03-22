from os import remove as remove_file
from os import environ
from os import rename
from os.path import join as join_path
from gzip import GzipFile

from requests import get as get_request
from requests import post as post_request

from genome_sort.exceptions import AnalysisNotFound


_ALLOWED_EXTENSIONS = set(['fastq'])
_ONECODEX_APIKEY = environ['ONE_CODEX_API_KEY']
_BASE_API_URL = "https://beta.onecodex.com/api/v0/"
_UPLOAD_FOLDER = '/tmp'


def change_file_name(filename,sample_id):
    filepath = join_path(_UPLOAD_FOLDER, filename)
    rename(filepath, filepath.replace(filename.rsplit('.', 1)[0],sample_id))


def is_allowed_file(filename):
    is_valid_filename = '.' in filename
    has_valid_extension = filename.rsplit('.', 1)[1] in _ALLOWED_EXTENSIONS
    is_allowed_file = is_valid_filename and has_valid_extension
    return is_allowed_file


def upload_genome_file(filename):
    absolute_filename = join_path(
        _UPLOAD_FOLDER,
        filename
    )
    files = {'file': open(absolute_filename, 'rb')}
    response = post_request(
        _BASE_API_URL + "upload",
        auth=(_ONECODEX_APIKEY, '',),
        files=files,
        allow_redirects=True,
    )
    return response.json()['sample_id']


def get_analyses():
    response = _get_request("analyses")
    return response.json()


def get_analysis_table_from_id(analysis_id):
    response = _get_request("analyses/{}/table".format(analysis_id))
    return response.json()


def format_analyses(analyses):
    formatted_analyses = []
    for analysis in analyses:
        if analysis['analysis_status'] == 'Success':
            css_class = 'success'
        elif analysis['analysis_status'] == 'Pending':
            css_class = 'secondary disabled'
        elif analysis['analysis_status'] == 'Failed':
            css_class = 'alert'
        else:
            css_class = 'disabled'

        formatted_analysis = {
            'id': analysis['id'],
            'css_class': css_class,
            'sample_filename': analysis['sample_filename'],
        }
        formatted_analyses.append(formatted_analysis)
    return formatted_analyses


def get_sample_id_from_analysis_id(analysis_id):
    analyses = get_analyses()
    for analysis in analyses:
        if analysis['id'] == analysis_id:
            return analysis['sample_id']
    raise AnalysisNotFound


def process_analysis(analysis_id):
    local_filename = _download_raw_analysis(analysis_id)

    local_unzipped_filename = join_path(
        _UPLOAD_FOLDER,
        'read_data_{}.tsv'.format(analysis_id),
    )
    _unzip_file(local_filename, local_unzipped_filename)

    remove_file(local_filename)
    return local_unzipped_filename


def _download_raw_analysis(analysis_id):
    local_filename = join_path(
        _UPLOAD_FOLDER,
        'raw_{}.tsv.gz'.format(analysis_id),
    )
    raw_analysis = get_request(
        '{}analyses/{}/raw'.format(_BASE_API_URL, analysis_id),
        auth=(_ONECODEX_APIKEY, ''),
        stream=True,
    )
    with open(local_filename, 'wb') as f:
        for chunk in raw_analysis.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
    return local_filename


def _unzip_file(gz_file, target_filename):
    unzipped_file = GzipFile(fileobj=open(gz_file, 'rb'))
    with open(target_filename, 'wb') as _file:
        _file.write(unzipped_file.read())


def _get_request(sub_url):
    response = get_request(
        _BASE_API_URL + sub_url,
        auth=(_ONECODEX_APIKEY, ''),
        allow_redirects=True,
    )
    return response
