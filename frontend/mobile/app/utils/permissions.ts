import { Camera } from "expo-camera";
import { Alert, Linking, Platform } from "react-native";

export async function requestCameraPermission(): Promise<boolean> {
  const { status } = await Camera.requestCameraPermissionsAsync();
  if (status === "granted") return true;

  Alert.alert(
    "Permiso de camara requerido",
    "VerifID necesita acceso a la camara para verificar tu identidad. Por favor, habilita el permiso en Ajustes.",
    [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Abrir Ajustes",
        onPress: () => {
          if (Platform.OS === "ios") {
            Linking.openURL("app-settings:");
          } else {
            Linking.openSettings();
          }
        },
      },
    ]
  );
  return false;
}

export async function checkCameraPermission(): Promise<boolean> {
  const { status } = await Camera.getCameraPermissionsAsync();
  return status === "granted";
}
