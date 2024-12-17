import asyncio
from datetime import datetime
from typing import Any, ClassVar, Mapping, Optional, Sequence, cast

from typing_extensions import Self
from viam.components.sensor import *
from viam.logging import getLogger
from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.proto.service.vision import Detection
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.services.vision import Vision
from viam.utils import SensorReading, struct_to_dict

LOGGER = getLogger(__name__)

class SbarroData(Sensor, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("brad-grigsby", "my-sbarro-sensor"), "sbarro-data"
    )

    def __init__(self, name, *, logger = None):
        super().__init__(name, logger=logger)
        self.machine = None
        self.viam_client = None
        self.vision_service = None
        self.connected = False

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        fields = config.attributes.fields
        if "base_camera_name" not in fields:
            raise Exception("Camera field is required")
        if "base_vision_name" not in fields:
            raise Exception("Vision field is required")
        
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.info("Reconfiguring " + self.name)
        self.DEPS = dependencies
        attrs = struct_to_dict(config.attributes)
        self.base_camera_name = str(attrs.get("base_camera_name", "camera-1"))
        self.base_vision_name = str(attrs.get("base_vision_name", "vision-1"))

        return super().reconfigure(config, dependencies)

    async def get_model_detection(
        self,
    ) -> Detection:
        actual_model = self.DEPS[Vision.get_resource_name(self.base_vision_name)]
        vision = cast(Vision, actual_model)
        detections = await vision.get_detections_from_camera(self.base_camera_name)

        return detections

    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, SensorReading]:
        # Get detections from the vision service
        detections = await self.get_model_detection()

        readings = []
        for detection in detections:
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            initial_timestamp = "_".join(detection.class_name.split("_")[2:])
            total_trays = int(detection.class_name.split("_")[1])
            readings.append({
                "current_timestamp": current_timestamp,
                "initial_timestamp": initial_timestamp,
                "total_trays": total_trays,
            })

        # ## ---- FAKE DATA ---- ##
        # readings = []
        # for _ in range(4):
        #     # fake_detection = "pizza_12_20241209_184330"
        #     fake_locations = ["Test", "Test2", "Test3"]
        #     current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     initial_timestamp = "202412" + str(random.randint(10, 15)) + "_" + str(random.randint(10, 23)) + str(random.randint(10, 59)) + str(random.randint(10, 59))
        #     total_trays = random.randint(0, 100)
        #     readings.append({
        #         "current_timestamp": current_timestamp,
        #         "initial_timestamp": initial_timestamp,
        #         "location_name": fake_locations[random.randint(0, 2)],
        #         "total_trays": total_trays,
        #     })

        return {"readings": readings}


if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())

