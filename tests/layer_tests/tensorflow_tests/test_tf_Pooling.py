# Copyright (C) 2018-2022 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from common.layer_test_class import check_ir_version
from common.tf_layer_test_class import CommonTFLayerTest

from unit_tests.utils.graph import build_graph


class TestPooling(CommonTFLayerTest):
    def create_pooling_net(self, kernel_size, strides, pads, in_shape, out_shape, method,
                           ir_version, use_new_frontend):
        """
            Tensorflow net                 IR net

            Input->Pooling        =>       Input->Pooling

        """

        #
        #   Create Tensorflow model
        #

        import tensorflow as tf

        tf.compat.v1.reset_default_graph()

        # Create the graph and model
        with tf.compat.v1.Session() as sess:

            pads_begin, pads_end, padding = pads

            # 4D tensors
            if len(in_shape) == 4:
                input_shape = [in_shape[0], in_shape[2], in_shape[3], in_shape[1]]
                input = tf.compat.v1.placeholder(tf.float32, input_shape, 'Input')

                stride = [1, strides[0], strides[1], 1]
                kernel = [1, kernel_size[0], kernel_size[1], 1]

                if method == 'max':
                    tf.nn.max_pool2d(input=input, ksize=kernel, strides=stride, padding=padding,
                                     name='Operation')
                elif method == 'avg':
                    tf.nn.avg_pool2d(input=input, ksize=kernel, strides=stride, padding=padding,
                                     name='Operation')

            # 5D tensors
            elif len(in_shape) == 5:
                input_shape = [in_shape[0], in_shape[2], in_shape[3], in_shape[4], in_shape[1]]
                input = tf.compat.v1.placeholder(tf.float32, input_shape, 'Input')

                stride = [1, strides[0], strides[1], strides[2], 1]
                kernel = [1, kernel_size[0], kernel_size[1], kernel_size[2], 1]

                if method == 'max':
                    tf.nn.max_pool3d(input, kernel, stride, padding,
                                     name='Operation')  # , data_format='NCHW')
                elif method == 'avg':
                    tf.nn.avg_pool3d(input, kernel, stride, padding,
                                     name='Operation')  # , data_format='NCHW')

            tf.compat.v1.global_variables_initializer()
            tf_net = sess.graph_def

        #
        #   Create reference IR net
        #   Please, specify 'type': 'Input' for input node
        #   Moreover, do not forget to validate ALL layer attributes!!!
        #

        ref_net = None

        if check_ir_version(10, None, ir_version) and not use_new_frontend:
            nodes_attributes = {
                'input': {'kind': 'op', 'type': 'Parameter'},
                'input_data': {'shape': in_shape, 'kind': 'data'},
                'pooling': {'kernel': kernel_size, 'pads_begin': pads_begin, 'pads_end': pads_end,
                            'strides': strides, 'kind': 'op', 'type': None},
                'pooling_data': {'shape': out_shape, 'kind': 'data'},
                'result': {'kind': 'op', 'type': 'Result'},
                'pooling_indicies_data': {'kind': 'data', 'shape': out_shape}
            }

            if method == 'avg':
                nodes_attributes['pooling']['type'] = 'AvgPool'
            elif method == 'max':
                nodes_attributes['pooling']['type'] = 'MaxPool'

            edges = [('input', 'input_data'),
                     ('input_data', 'pooling'),
                     ('pooling', 'pooling_data', {'out': 0}),
                     ('pooling_data', 'result')]

            if method == 'max':
                edges.append(('pooling', 'pooling_indicies_data', {'out': 1}))

            ref_net = build_graph(nodes_attributes,
                                  edges=edges,
                                  nodes_with_edges_only=True)

        return tf_net, ref_net

    test_data_4D = []
    for method in ['max', 'avg']:
        test_data_4D.extend([dict(kernel_size=[1, 1], strides=[1, 1], pads=[[0, 0], [0, 0], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 224, 224],
                                  method=method),
                             dict(kernel_size=[2, 2], strides=[2, 2], pads=[[0, 0], [0, 0], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 112],
                                  method=method),
                             dict(kernel_size=[2, 4], strides=[2, 4], pads=[[0, 0], [0, 0], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 56],
                                  method=method),
                             dict(kernel_size=[4, 2], strides=[4, 2], pads=[[0, 0], [0, 0], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 56, 112],
                                  method=method),
                             dict(kernel_size=[2, 3], strides=[2, 3], pads=[[0, 0], [0, 1], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 75],
                                  method=method),
                             dict(kernel_size=[3, 2], strides=[3, 2], pads=[[0, 0], [1, 0], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 75, 112],
                                  method=method),
                             dict(kernel_size=[3, 3], strides=[2, 2], pads=[[0, 0], [1, 1], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 112],
                                  method=method),
                             dict(kernel_size=[3, 2], strides=[2, 2], pads=[[0, 0], [1, 0], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 112],
                                  method=method),
                             dict(kernel_size=[2, 3], strides=[2, 3], pads=[[0, 0], [0, 1], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 75],
                                  method=method),
                             dict(kernel_size=[111, 111], strides=[111, 111],
                                  pads=[[54, 54], [55, 55], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 3, 3], method=method),
                             dict(kernel_size=[111, 113], strides=[111, 113],
                                  pads=[[54, 1], [55, 1], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 3, 2], method=method),
                             dict(kernel_size=[113, 113], strides=[113, 113],
                                  pads=[[1, 1], [1, 1], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 2, 2], method=method),
                             dict(kernel_size=[113, 113], strides=[111, 111],
                                  pads=[[55, 55], [56, 56], 'SAME'],
                                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 3, 3],
                                  method=method)])

        test_data_4D.extend(
            [dict(kernel_size=[1, 1], strides=[1, 1], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 224, 224], method=method),
             dict(kernel_size=[2, 2], strides=[2, 2], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 112], method=method),
             dict(kernel_size=[2, 4], strides=[2, 4], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 56], method=method),
             dict(kernel_size=[4, 2], strides=[4, 2], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 56, 112], method=method),
             dict(kernel_size=[2, 3], strides=[2, 3], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 74], method=method),
             dict(kernel_size=[3, 2], strides=[3, 2], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 74, 112], method=method),
             dict(kernel_size=[3, 3], strides=[2, 2], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 111, 111], method=method),
             dict(kernel_size=[3, 2], strides=[2, 2], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 111, 112], method=method),
             dict(kernel_size=[2, 3], strides=[2, 3], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 112, 74], method=method),
             dict(kernel_size=[111, 111], strides=[111, 111], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 2, 2], method=method),
             dict(kernel_size=[111, 113], strides=[111, 113], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 2, 1], method=method),
             dict(kernel_size=[113, 113], strides=[113, 113], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 1, 1], method=method),
             dict(kernel_size=[113, 113], strides=[111, 111], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 2, 2], method=method),
             dict(kernel_size=[224, 224], strides=[1, 1], pads=[[0, 0], [0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224], out_shape=[1, 3, 1, 1], method=method)])

    @pytest.mark.parametrize("params", test_data_4D)
    @pytest.mark.nightly
    def test_pool_4D(self, params, ie_device, precision, ir_version, temp_dir, use_new_frontend,
                     api_2):
        self._test(*self.create_pooling_net(**params, ir_version=ir_version,
                                            use_new_frontend=use_new_frontend),
                   ie_device, precision, ir_version, temp_dir=temp_dir,
                   use_new_frontend=use_new_frontend, api_2=api_2)

    test_data_5D = []
    for method in ['max', 'avg']:
        test_data_5D.extend(
            [dict(kernel_size=[1, 1, 1], strides=[1, 1, 1], pads=[[0, 0, 0], [0, 0, 0], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 224, 224, 224], method=method),
             dict(kernel_size=[2, 2, 2], strides=[2, 2, 2], pads=[[0, 0, 0], [0, 0, 0], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 112], method=method),
             dict(kernel_size=[2, 2, 4], strides=[2, 2, 4], pads=[[0, 0, 0], [0, 0, 0], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 56], method=method),
             dict(kernel_size=[4, 2, 2], strides=[4, 2, 2], pads=[[0, 0, 0], [0, 0, 0], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 56, 112, 112], method=method),
             dict(kernel_size=[2, 2, 3], strides=[2, 2, 3], pads=[[0, 0, 0], [0, 0, 1], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 75], method=method),
             dict(kernel_size=[3, 2, 2], strides=[3, 2, 2], pads=[[0, 0, 0], [1, 0, 0], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 75, 112, 112], method=method),
             dict(kernel_size=[3, 3, 3], strides=[2, 2, 2], pads=[[0, 0, 0], [1, 1, 1], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 112], method=method),
             dict(kernel_size=[3, 2, 2], strides=[2, 2, 2], pads=[[0, 0, 0], [1, 0, 0], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 112], method=method),
             dict(kernel_size=[2, 2, 3], strides=[2, 2, 3], pads=[[0, 0, 0], [0, 0, 1], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 75], method=method),
             dict(kernel_size=[111, 111, 111], strides=[111, 111, 111],
                  pads=[[54, 54, 54], [55, 55, 55], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 3, 3, 3], method=method),
             dict(kernel_size=[111, 111, 113], strides=[111, 111, 113],
                  pads=[[54, 54, 1], [55, 55, 1], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 3, 3, 2], method=method),
             dict(kernel_size=[113, 113, 113], strides=[113, 113, 113],
                  pads=[[1, 1, 1], [1, 1, 1], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 2, 2, 2], method=method),
             dict(kernel_size=[113, 113, 113], strides=[111, 111, 111],
                  pads=[[55, 55, 55], [56, 56, 56], 'SAME'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 3, 3, 3], method=method)])

        test_data_5D.extend(
            [dict(kernel_size=[1, 1, 1], strides=[1, 1, 1], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 224, 224, 224], method=method),
             dict(kernel_size=[2, 2, 2], strides=[2, 2, 2], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 112], method=method),
             dict(kernel_size=[2, 2, 4], strides=[2, 2, 4], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 56], method=method),
             dict(kernel_size=[4, 2, 2], strides=[4, 2, 2], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 56, 112, 112], method=method),
             dict(kernel_size=[2, 2, 3], strides=[2, 2, 3], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 74], method=method),
             dict(kernel_size=[3, 2, 2], strides=[3, 2, 2], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 74, 112, 112], method=method),
             dict(kernel_size=[3, 3, 3], strides=[2, 2, 2], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 111, 111, 111], method=method),
             dict(kernel_size=[3, 2, 2], strides=[2, 2, 2], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 111, 112, 112], method=method),
             dict(kernel_size=[2, 2, 3], strides=[2, 2, 3], pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 112, 112, 74], method=method),
             dict(kernel_size=[111, 111, 111], strides=[111, 111, 111],
                  pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 2, 2, 2], method=method),
             dict(kernel_size=[111, 111, 113], strides=[111, 111, 113],
                  pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 2, 2, 1], method=method),
             dict(kernel_size=[113, 113, 113], strides=[113, 113, 113],
                  pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 1, 1, 1], method=method),
             dict(kernel_size=[113, 113, 113], strides=[111, 111, 111],
                  pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 2, 2, 2], method=method),
             dict(kernel_size=[224, 224, 224], strides=[1, 1, 1],
                  pads=[[0, 0, 0], [0, 0, 0], 'VALID'],
                  in_shape=[1, 3, 224, 224, 224], out_shape=[1, 3, 1, 1, 1], method=method)])

    @pytest.mark.parametrize("params", test_data_5D)
    @pytest.mark.nightly
    def test_pool_5D(self, params, ie_device, precision, ir_version, temp_dir, use_new_frontend,
                     api_2):
        if ie_device == 'GPU':
            pytest.skip("5D tensors is not supported on GPU")
        self._test(*self.create_pooling_net(**params, ir_version=ir_version,
                                            use_new_frontend=use_new_frontend),
                   ie_device, precision, ir_version, temp_dir=temp_dir,
                   use_new_frontend=use_new_frontend, api_2=api_2)
