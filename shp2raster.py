# coding:utf-8
import sys
from osgeo import gdal, ogr
import cv2
import numpy


def shp2raster(input_shp, input_img, output_raster, rasterize_field, rasterize_type='binary'):
    """
    :brief 实现矢量转栅格功能,可选结果类型为二值栅格图，分类栅格图。
    :param input_shp: shape文件的绝对路径
    :param output_raster: 结果图的绝对路径
    :param rasterize_field: 栅格化指定的字段
    :param rasterize_type: 栅格化类型，binary为二值图，category为根据指定字段生成的分类图。
    :return: None
    """

    # 字段名称必须是str类型且不能为空，否则无法进行正确的栅格化
    if isinstance(rasterize_field, str) is False or rasterize_field is None:
        raise ValueError("Rasterize field name must be string type")

    # 打开shp文件
    source_ds = ogr.Open(input_shp)
    if source_ds is None:
        raise NameError("Open shape file failed.")
    source_layer = source_ds.GetLayer(0)

    raster_src = gdal.Open(input_img)
    geo = raster_src.GetGeoTransform()
    # 设置栅格化所需各种参数，创建栅格
    spatial_ref = source_layer.GetSpatialRef()
    x_min, y_min = geo[0], geo[3]
    pixel_size_x, pixel_size_y = geo[1], geo[5]

    target_ds = gdal.GetDriverByName('GTiff').Create(output_raster, raster_src.RasterXSize, raster_src.RasterYSize, 1, gdal.GDT_Byte)

    # 若待转换矢量数据存在空间参考则将栅格数据设置同样参考，否则不设置
    if spatial_ref is not None:
        target_ds.SetProjection(spatial_ref.ExportToWkt())

    target_ds.SetGeoTransform((x_min, pixel_size_x, 0, y_min, 0, pixel_size_y))

    # 寻找属性表中是否包含指定的栅格化字段
    index = source_layer.GetLayerDefn().GetFieldIndex(rasterize_field)
    if index < 0:
        raise ValueError("Can't find the {} field, please check the shape file.".format(rasterize_field))

    # 生成二值图
    if rasterize_type == 'binary':
        gdal.RasterizeLayer(target_ds, [1], source_layer,
                            options=["ATTRIBUTE={}".format(rasterize_field)])
        band = target_ds.GetRasterBand(1)
        bdarr = band.ReadAsArray()
        bdarr[bdarr != 0] = 255
        band.WriteArray(bdarr)
        band.FlushCache()
    # 生成分类图
    elif rasterize_type == 'category':
        gdal.RasterizeLayer(target_ds, [1], source_layer, burn_values=[0],
                            options=["ATTRIBUTE={}".format(rasterize_field)])
    else:
        raise ValueError("Rasterize type must be one of binary and category.")

    print("Rasterize process success.")


if __name__ == "__main__":
    inputshp = sys.argv[1]
    input_img = sys.argv[2]
    outputraster = sys.argv[3]
    rasterizefield = 'id'
    rasterizetype = 'category'
    shp2raster(inputshp, input_img, outputraster, rasterizefield, rasterizetype)
