import os

from ..utils import get_or_make_label_encoder, cluster_alphnum
from ..special_tokens import TRAIN, EVAL, PREDICT
from ..read_write_tfrecord import write_single_problem_chunk_tfrecord
from ..bert_preprocessing.create_bert_features import create_pretraining_generator
from ..bert_preprocessing.tokenization import FullTokenizer


def preprocessing_fn(func):
    def wrapper(params, mode, get_data_num=False, write_tfrecord=True):
        problem = func.__name__

        if params.problem_type[problem] != 'pretrain':
            tokenizer = FullTokenizer(
                vocab_file=params.vocab_file, do_lower_case=True)
            inputs_list, target_list = func(params, mode)

            label_encoder = get_or_make_label_encoder(
                params, problem=problem, mode=mode, label_list=target_list)

            if get_data_num:
                return len(inputs_list), len(label_encoder.encode_dict)

            if mode == PREDICT:
                return inputs_list, target_list, label_encoder
            
            if write_tfrecord:
                return write_single_problem_chunk_tfrecord(
                    func.__name__,
                    inputs_list,
                    target_list,
                    label_encoder,
                    params,
                    tokenizer,
                    mode)
            else:
                return {
                    'problem': func.__name__,
                    'inputs_list': inputs_list,
                    'target_list': target_list,
                    'label_encoder':label_encoder,
                    'tokenizer':tokenizer
                }
        else:
            tokenizer = FullTokenizer(
                vocab_file=params.vocab_file, do_lower_case=True)
            inputs_list = func(params, mode)

            params.num_classes['next_sentence'] = 2
            params.problem_type['next_sentence'] = 'cls'
            return create_pretraining_generator(func.__name__,
                                                inputs_list,
                                                None,
                                                None,
                                                params,
                                                tokenizer)

    return wrapper
