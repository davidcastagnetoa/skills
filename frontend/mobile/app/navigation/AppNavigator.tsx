import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";

import WelcomeScreen from "../screens/WelcomeScreen";
import SelfieCaptureScreen from "../screens/SelfieCapture";
import ActiveChallengesScreen from "../screens/ActiveChallenges";
import DocumentCaptureScreen from "../screens/DocumentCapture";
import ProcessingScreen from "../screens/ProcessingScreen";
import ResultScreen from "../screens/ResultScreen";

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Welcome"
        screenOptions={{
          headerShown: false,
          animation: "slide_from_right",
        }}
      >
        <Stack.Screen name="Welcome" component={WelcomeScreen} />
        <Stack.Screen name="SelfieCapture" component={SelfieCaptureScreen} />
        <Stack.Screen
          name="ActiveChallenges"
          component={ActiveChallengesScreen}
        />
        <Stack.Screen
          name="DocumentCapture"
          component={DocumentCaptureScreen}
        />
        <Stack.Screen name="Processing" component={ProcessingScreen} />
        <Stack.Screen name="Result" component={ResultScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
