import unreal
import os
def ImportSkeletalMesh(meshPath):
    
    importTask = unreal.AssetImportTask()
    importTask.filename = meshPath
    assetName = os.path.basename(os.path.abspath(meshPath)).split(".")[0]
    importTask.destination_path = '/game/' + assetName
    importTask.automated = True # do not popup the import options
    importTask.save = True
    importTask.replace_existing = True

    importOptions = unreal.FbxImportUI()
    importOptions.import_mesh = True
    importOptions.import_as_skeletal = True
    importOptions.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
    importOptions.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose', True)

    importTask.options = importOptions

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])
    return importTask.get_objects()[0]


ImportSkeletalMesh("C:/Users/jili1/Downloads/out/Alex.fbx")