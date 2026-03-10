import React from "react";
import { View, StyleSheet } from "react-native";
import { Button, Text } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";

interface Props {
  title?: string;
  message: string;
  retryTarget?: keyof RootStackParamList;
}

export default function ErrorScreen({
  title = "Ha ocurrido un error",
  message,
  retryTarget,
}: Props) {
  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.icon}>{"\u26A0"}</Text>
        <Text variant="headlineSmall" style={styles.title}>
          {title}
        </Text>
        <Text variant="bodyLarge" style={styles.message}>
          {message}
        </Text>
        <View style={styles.buttons}>
          {retryTarget && (
            <Button
              mode="contained"
              onPress={() => navigation.navigate(retryTarget as any)}
              style={styles.button}
            >
              Reintentar
            </Button>
          )}
          <Button
            mode={retryTarget ? "outlined" : "contained"}
            onPress={() => navigation.navigate("Welcome")}
            style={styles.button}
          >
            Volver al inicio
          </Button>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  content: { flex: 1, padding: 24, justifyContent: "center", alignItems: "center" },
  icon: { fontSize: 48, marginBottom: 16, color: "#d32f2f" },
  title: { textAlign: "center", fontWeight: "bold", marginBottom: 8 },
  message: { textAlign: "center", color: "#666", marginBottom: 32 },
  buttons: { gap: 12, width: "100%" },
  button: { borderRadius: 8 },
});
