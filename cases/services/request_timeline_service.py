from cases.models import RequestTimeline, ServiceRequest


class RequestTimelineService:

    @staticmethod
    def record(
        *,
        service_request: ServiceRequest,
        event_type: str,
        title: str,
        description: str = "",
        actor=None,
        metadata: dict | None = None,
    ) -> RequestTimeline:
        if event_type not in RequestTimeline.EventType.values:
            raise ValueError("نوع رویداد نامعتبر است.")

        title = title.strip()

        if not title:
            raise ValueError("عنوان رویداد الزامی است.")

        return RequestTimeline.objects.create(
            service_request=service_request,
            event_type=event_type,
            title=title,
            description=description.strip(),
            actor=actor,
            metadata=metadata or {},
        )