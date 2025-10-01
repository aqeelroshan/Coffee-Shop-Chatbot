import { Text, View, TouchableOpacity, ScrollView, StatusBar } from 'react-native'
import React from 'react'
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { router } from 'expo-router'
import { useLocalSearchParams } from "expo-router";
import PageHeader from '@/components/PageHeader';
import { useCart } from '@/components/CartContext';
import DescriptionSection from '@/components/DescriptionSection';
import SizesSection from '@/components/SizesSection';
import DetailsHeader from '@/components/DetailsHeader';
import { SafeAreaView } from 'react-native-safe-area-context';
//import Toast from 'react-native-simple-toast';
import { useToast } from "react-native-toast-notifications";


const DetailsPage = () => {
    const toast = useToast();
    const { addToCart } = useCart();
    const { name, image_url, type, description, price, rating } = useLocalSearchParams() as { name: string, image_url: string, type: string, description: string, price: string, rating: string };

    // const buyNow = () => {
    //     addToCart(name, 1);
    //     Toast.show(`${name} added to cart`, Toast.SHORT);
    //     router.back();
    // };
    const buyNow = () => {
        addToCart(name, 1);

        toast.show(`${name} added to cart`, {
            type: "success",
            placement: "bottom",
            duration: 2000, // ~ Toast.SHORT
        });

        router.back();
    };




    return (
        <GestureHandlerRootView
            className='bg-[#F9F9F9] w-full h-full'
        >
            <StatusBar backgroundColor="white" />

            <PageHeader title="Detail" showHeaderRight={true} bgColor='#F9F9F9' />

            <View className='h-full flex-col justify-between'>
                <ScrollView>
                    <View className='mx-5 items-center'>
                        <DetailsHeader image_url={image_url} name={name} type={type} rating={Number(rating)} />
                        <DescriptionSection description={description} />
                        <SizesSection />
                    </View>
                </ScrollView>
                <SafeAreaView className="flex-1 justify-end px-5">
                    <View
                        className='flex-row justify-between bg-white rounded-tl-3xl rounded-tr-3xl px-6 pt-3 pb-6'
                    >
                        <View>
                            <Text
                                className="text-[#A2A2A2] text-base font-[Sora-Regular] pb-3"
                            >Price
                            </Text>
                            <Text
                                className="text-app_orange_color text-2xl font-[Sora-SemiBold]"
                            >$ {price}
                            </Text>
                        </View>

                        <TouchableOpacity
                            className="bg-app_orange_color w-[70%] rounded-3xl items-center justify-center"
                            onPress={buyNow}
                        >
                            <Text className="text-xl color-white font-[Sora-Regular]">Buy Now</Text>
                        </TouchableOpacity>

                    </View>
                </SafeAreaView>

            </View>


        </GestureHandlerRootView>
    )
}

export default DetailsPage

