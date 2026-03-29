import numpy as np
import tensorflow as tf
import cv2
import os

from keras.models import load_model
from keras.applications.vgg16 import preprocess_input
from keras.preprocessing import image
from keras import Model
from keras.layers import InputLayer, Conv2D, SeparableConv2D, DepthwiseConv2D
from keras.mixed_precision import Policy
from utils.config import MODEL_PATH


CLASS_LABELS = [
    "Covid-19",
    "Normal",
    "Pneumonia-Bacterial",
    "Pneumonia-Viral",
]

class PatchedInputLayer(InputLayer):
    @classmethod
    def from_config(cls, config):
        if "batch_shape" in config and "batch_input_shape" not in config:
            config["batch_input_shape"] = config.pop("batch_shape")
        return super().from_config(config)


def load_compatible_model(model_path: str):
    custom_objects = {
        "InputLayer": PatchedInputLayer,
        # Newer model exports may serialize dtype as DTypePolicy.
        "DTypePolicy": Policy,
    }
    try:
        return load_model(
            model_path,
            compile=False,
            custom_objects=custom_objects,
        )
    except TypeError as exc:
        if "Unrecognized keyword arguments: ['batch_shape']" not in str(exc):
            raise
        return load_model(
            model_path,
            compile=False,
            custom_objects=custom_objects,
        )


model = None
model_load_error = None


def get_model():
    global model, model_load_error
    if model is not None:
        return model
    if model_load_error is not None:
        raise RuntimeError(model_load_error)

    try:
        model = load_compatible_model(str(MODEL_PATH))
        return model
    except Exception as exc:
        model_load_error = (
            f"Failed to load model from {MODEL_PATH}. "
            "The file appears to be saved with a different Keras/TensorFlow "
            f"serialization format. Original error: {exc}"
        )
        raise RuntimeError(model_load_error) from exc


# -------------------------------------
# 🔹 Preprocess Image (VGG16 style)
# -------------------------------------
def preprocess_image(image_path: str):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)

    # Expand batch dimension
    img_array = np.expand_dims(img_array, axis=0)

    # IMPORTANT: VGG16 preprocessing
    img_array = preprocess_input(img_array)

    return img_array


# -------------------------------------
# 🔹 Prediction
# -------------------------------------
def predict(image_path):
    loaded_model = get_model()
    img_array = preprocess_image(image_path)

    prediction = loaded_model.predict(img_array, verbose=0)

    class_index = int(np.argmax(prediction))
    confidence = float(np.max(prediction))

    if class_index < len(CLASS_LABELS):
        predicted_class = CLASS_LABELS[class_index]
    else:
        predicted_class = f"Class-{class_index}"

    heatmap_path = generate_gradcam(
        loaded_model,
        img_array,
        image_path,
        class_index
    )

    return predicted_class, confidence, heatmap_path


# -------------------------------------
# 🔥 Grad-CAM
# -------------------------------------
def _resolve_last_conv_layer_name(model, preferred_name="block5_conv3"):
    if preferred_name:
        try:
            model.get_layer(preferred_name)
            return preferred_name
        except Exception:
            pass

    conv_types = (Conv2D, SeparableConv2D, DepthwiseConv2D)
    for layer in reversed(model.layers):
        if isinstance(layer, conv_types):
            return layer.name

    for layer in reversed(model.layers):
        shape = getattr(layer, "output_shape", None)
        if isinstance(shape, tuple) and len(shape) == 4:
            return layer.name

    raise ValueError("No 2D convolution layer found for Grad-CAM generation.")


def generate_gradcam(
    model,
    img_array,
    image_path,
    class_index,
    last_conv_layer_name="block5_conv3"
):
    last_conv_layer_name = _resolve_last_conv_layer_name(model, last_conv_layer_name)

    grad_model = Model(
        inputs=[model.input],
        outputs=[model.get_layer(last_conv_layer_name).output, model.output],
    )

    with tf.GradientTape() as tape:
        try:
            conv_outputs, predictions = grad_model(img_array)
        except Exception:
            conv_outputs, predictions = grad_model([[img_array]])

        if isinstance(conv_outputs, (list, tuple)):
            conv_outputs = conv_outputs[0]
        if isinstance(predictions, (list, tuple)):
            predictions = predictions[0]

        loss = predictions[:, class_index]

    grads = tape.gradient(loss, conv_outputs)

    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = tf.reduce_sum(pooled_grads * conv_outputs, axis=-1)

    heatmap = tf.maximum(heatmap, 0)
    heatmap /= tf.reduce_max(heatmap) + 1e-8

    heatmap = heatmap.numpy()

    original_img = cv2.imread(image_path)
    original_img = cv2.resize(original_img, (224, 224))

    heatmap = cv2.resize(heatmap, (224, 224))
    heatmap = np.uint8(255 * heatmap)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    superimposed_img = cv2.addWeighted(original_img, 0.6, heatmap, 0.4, 0)

    base = image_path.rsplit(".", 1)[0]
    heatmap_path = f"{base}_heatmap.jpg"

    cv2.imwrite(heatmap_path, superimposed_img)
    print("Prediction shape:", predictions.shape)
    print("Class index:", class_index)

    return heatmap_path
