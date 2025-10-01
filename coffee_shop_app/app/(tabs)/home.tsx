import { useEffect, useState } from 'react';
import { Product, ProductCategory } from '@/types/types';
import { fetchProducts } from '@/services/productService';
import { Text, View, Image, FlatList, StatusBar, TouchableOpacity, Alert } from 'react-native'
import React from 'react'
import { SafeAreaView } from 'react-native-safe-area-context'
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { router } from "expo-router";
import AntDesign from '@expo/vector-icons/AntDesign';
;
import { useCart } from '@/components/CartContext';
import Banner from '@/components/Banner';
import SearchArea from '@/components/SearchArea';

//import Toast from 'react-native-simple-toast';
import { useToast } from "react-native-toast-notifications";

const Home = () => {

    const toast = useToast();
    const { addToCart, cartItems } = useCart();


    const [products, setProducts] = useState<Product[]>([]);
    const [shownProducts, setShownProducts] = useState<Product[]>([]);
    const [productCategories, setProductCatgories] = useState<ProductCategory[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [selectedCategory, setSelectedCategory] = useState<string>('All');

    useEffect(() => {
        const uniqueCategories = Array.from((productCategories)).map((category) => ({
            id: category.id,
            selected: selectedCategory === category.id,
        }));
        setProductCatgories(uniqueCategories);
        if (selectedCategory === 'All') {
            setShownProducts(products);
        } else {
            const filteredProducts = products.filter((product) => product.category === selectedCategory);
            setShownProducts(filteredProducts);
        }
    }, [selectedCategory])



    useEffect(() => {
        const loadProducts = async () => {
            try {
                const productsData = await fetchProducts();


                const categories = productsData.map((product) => product.category);
                categories.unshift('All');

                const uniqueCategories = Array.from(new Set(categories)).map((category) => ({
                    id: category,
                    selected: selectedCategory === category,
                }));


                setProductCatgories(uniqueCategories);
                setProducts(productsData);
                setShownProducts(productsData)



            } catch (err) {
                console.error("❌ Error loading products:", err);
            } finally {
                setLoading(false)
            }
        }
        loadProducts();
    }, [])

    if (loading) return <Text>Loading....</Text>

    // const addButton = (name: string) => {
    //     addToCart(name, 1);

    //     // Simple, reliable toast that won't get stuck
    //     Toast.show(`${name} added to cart`, Toast.SHORT);
    // };

    const addButton = (name: string) => {
        addToCart(name, 1);

        toast.show(`${name} added to cart`, {
            type: "success",    // can be "normal", "success", "warning", "danger"
            placement: "bottom", // top | center | bottom
            duration: 2000,      // 2 seconds
        });
    };





    // const addButton = (name: string) => {
    //     addToCart(name, 1);
    //     Toast.show(`${name} added to cart`, {
    //         duration: Toast.durations.SHORT,
    //     });
    // };



    return (
        <GestureHandlerRootView>
            <SafeAreaView
                className='w-full h-full'
            >
                <FlatList
                    horizontal={false}
                    columnWrapperStyle={{ justifyContent: 'space-between', marginLeft: 15, marginRight: 15 }}
                    numColumns={2}
                    keyExtractor={(item, index) => index.toString()}
                    data={shownProducts}

                    renderItem={({ item }) => (
                        <View
                            className='w-[48%] mt-2 bg-white rounded-2xl p-2 flex justify-between'
                        >
                            <TouchableOpacity
                                onPress={() => {

                                    router.push({
                                        pathname: '/details', params: {
                                            name: item.name,
                                            image_url: item.image_url,
                                            type: item.category,
                                            price: item.price,
                                            rating: item.rating,
                                            description: item.description,
                                        }
                                    })
                                }
                                }
                            >
                                <Image
                                    source={{ uri: item.image_url }}
                                    className='w-full h-32 rounded-2xl'
                                />

                                <Text
                                    className="text-[#242424] text-lg font-[Sora-SemiBold] ml-1 mt-2"
                                >   {item.name}
                                </Text>

                                <Text
                                    className="text-[#A2A2A2] text-sm font-[Sora-Regular] ml-1 mt-2"
                                >{item.category}
                                </Text>
                            </TouchableOpacity>

                            <View
                                className="flex-row justify-between ml-1 mt-4 mb-2"
                            >
                                <Text
                                    className="text-[#050505] text-xl font-[Sora-SemiBold] "
                                >
                                    ${item.price}
                                </Text>

                                <TouchableOpacity
                                    onPress={() => addButton(item.name)}
                                    activeOpacity={1.0}

                                >
                                    <View
                                        className='mr-2 p-2 -mt-1 bg-app_orange_color rounded-xl'
                                    >
                                        <AntDesign name="plus" size={20} color="white" />
                                    </View>
                                </TouchableOpacity>

                            </View>

                        </View>
                    )}

                    ListHeaderComponent={() => (
                        <View className='flex'>
                            <SearchArea />
                            <Banner />
                            <View
                                className='flex items-center'
                            >
                                <FlatList
                                    className='mt-6 w-[90%] mb-2'
                                    data={productCategories}
                                    horizontal={true}
                                    renderItem={({ item }) => (
                                        <TouchableOpacity
                                            onPress={() => setSelectedCategory(item.id)}
                                        >
                                            <Text
                                                className={`text-sm mr-4 font-[Sora-Regular] p-3 rounded-lg 
                                                ${item.selected ? 'text-white' : 'text-[#313131]'}
                                                ${item.selected ? 'bg-app_orange_color ' : 'bg-[#EDEDED] '}
                                                `}
                                            >{item.id}
                                            </Text>

                                        </TouchableOpacity>
                                    )}
                                />
                            </View>



                        </View>
                    )}


                />


            </SafeAreaView>



        </GestureHandlerRootView>

    )
}

export default Home
