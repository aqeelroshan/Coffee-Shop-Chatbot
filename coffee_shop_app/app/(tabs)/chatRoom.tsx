import { Alert, TouchableOpacity, View, Text, TextInput, KeyboardAvoidingView, Platform } from 'react-native'
import React, { useEffect, useRef, useState } from 'react'
import { StatusBar } from 'expo-status-bar'
import MessageList from '@/components/MessageList'
import { MessageInterface } from '@/types/types';
import { widthPercentageToDP as wp, heightPercentageToDP as hp } from 'react-native-responsive-screen'
import { GestureHandlerRootView } from 'react-native-gesture-handler'
import { Feather } from '@expo/vector-icons'
import { callChatBotAPI } from '@/services/chatBot'
import PageHeader from '@/components/PageHeader'
import { useCart } from '@/components/CartContext'

const ChatRoom = () => {

    const { addToCart, emptyCart } = useCart();

    const [messages, setMessages] = useState<MessageInterface[]>([]);
    const [isTyping, setIsTyping] = useState<boolean>(false);
    //const textRef = useRef('')
    const [text, setText] = useState('');
    const inputRef = useRef<TextInput>(null)


    useEffect(() => {
    }, [messages]);

    const handleSendMessage = async () => {
        let message = text.trim();
        if (!message) return;
        try {

            // Add the user message to the list of messages
            let InputMessages = [...messages, { content: message, role: 'user' }];

            setMessages(InputMessages);
            setText('');
            if (inputRef) inputRef?.current?.clear();
            setIsTyping(true)
            let resposnseMessage = await callChatBotAPI(InputMessages);
            setIsTyping(false)
            setMessages(prevMessages => [...prevMessages, resposnseMessage]);

            if (resposnseMessage) {
                if (resposnseMessage.memory) {
                    if (resposnseMessage.memory.order) {
                        emptyCart()
                        resposnseMessage.memory.order.forEach((item: any) => {
                            addToCart(item.item, item.quantity)
                        });
                    }
                }
            }


        } catch (err: any) {
            Alert.alert('Message', err.message)
        }

    }




    return (
        <GestureHandlerRootView>
            <StatusBar style='dark' />

            <View
                className='flex-1 bg-white'
            >

                <PageHeader title="Chat Bot" showHeaderRight={false} bgColor='white' />

                <View className='h-3 border-b border-neutral-300' />
                {/* 👇 KeyboardAvoidingView handles keyboard overlap */}
                <KeyboardAvoidingView
                    style={{ flex: 1 }}
                    behavior={Platform.OS === "ios" ? "padding" : "height"}
                    keyboardVerticalOffset={hp(7)} // adjust this if header overlaps
                >

                    <View
                        className='flex-1 justify-between bg-neutral-100 overflow-visibile'
                    >
                        <View
                            className='flex-1'
                        >
                            <MessageList
                                messages={messages}
                                isTyping={isTyping}

                            />
                        </View>

                        <View
                            style={{ marginBottom: hp(9) }}
                            className='pt-2'
                        >
                            <View
                                className="flex-row mx-3 justify-between border p-2 bg-white border-neutral-300  rounded-full pl-5"
                            >
                                <TextInput
                                    ref={inputRef}
                                    value={text}
                                    onChangeText={setText}
                                    placeholder='Type message...'
                                    style={{ fontSize: hp(2) }}
                                    className='flex-1 mr2'
                                />
                                <TouchableOpacity
                                    onPress={handleSendMessage}
                                    className='bg-neutral-200 p-2 mr-[1px] rounded-full'
                                >
                                    <Feather name="send" size={hp(2.7)} color="#737373" />
                                </TouchableOpacity>
                            </View>
                        </View>
                    </View>


                </KeyboardAvoidingView>
            </View>
        </GestureHandlerRootView>
    )
}

export default ChatRoom

